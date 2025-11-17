module Image exposing (Model, Msg(..), init, update, view)

import Browser.Dom as Dom
import File exposing (File)
import Html exposing (..)
import Html.Attributes exposing (..)
import Html.Events exposing (..)
import Http
import Json.Decode as Decode
import Json.Encode as Encode
import Task
import Process


-- MODEL


type alias Model =
    { models : List ImageModel
    , selectedModel : Maybe ImageModel
    , parameters : List Parameter
    , isGenerating : Bool
    , outputImage : Maybe String
    , error : Maybe String
    , searchQuery : String
    , selectedCollection : String
    , requiredFields : List String
    , pollingImageId : Maybe Int
    , imageStatus : String
    , selectedVersion : Maybe String
    , uploadingFile : Maybe String  -- Track which parameter key is uploading
    }


type alias Parameter =
    { key : String
    , value : String
    , paramType : String
    , enum : Maybe (List String)
    , description : Maybe String
    , default : Maybe String
    , minimum : Maybe Float
    , maximum : Maybe Float
    , format : Maybe String
    }


type alias ImageModel =
    { id : String
    , name : String
    , description : String
    , inputSchema : Maybe Decode.Value
    }


type alias ImageRecord =
    { id : Int
    , prompt : String
    , imageUrl : String
    , modelId : String
    , createdAt : String
    , status : String
    }


init : ( Model, Cmd Msg )
init =
    ( { models = []
      , selectedModel = Nothing
      , parameters = []
      , isGenerating = False
      , outputImage = Nothing
      , error = Nothing
      , searchQuery = ""
      , selectedCollection = "text-to-image"
      , requiredFields = []
      , pollingImageId = Nothing
      , imageStatus = ""
      , selectedVersion = Nothing
      , uploadingFile = Nothing
      }
    , fetchModels "text-to-image"
    )


-- UPDATE


type Msg
    = NoOp
    | FetchModels
    | SelectCollection String
    | ModelsFetched (Result Http.Error (List ImageModel))
    | SelectModel String
    | SchemaFetched String (Result Http.Error { schema : Decode.Value, required : List String, version : Maybe String })
    | UpdateParameter String String
    | UpdateSearch String
    | GenerateImage
    | ImageGenerated (Result Http.Error { image_id : Int, status : String })
    | NavigateToImage Int
    | PollImageStatus
    | ImageStatusFetched (Result Http.Error ImageRecord)
    | ScrollToModel (Result Dom.Error ())
    | FileSelected String File
    | ImageUploaded String (Result Http.Error String)


update : Msg -> Model -> ( Model, Cmd Msg )
update msg model =
    case msg of
        NoOp ->
            ( model, Cmd.none )

        FetchModels ->
            ( model, fetchModels model.selectedCollection )

        SelectCollection collection ->
            ( { model | selectedCollection = collection, selectedModel = Nothing, outputImage = Nothing, requiredFields = [], selectedVersion = Nothing }
            , fetchModels collection
            )

        ModelsFetched result ->
            case result of
                Ok models ->
                    ( { model | models = models, error = Nothing }, Cmd.none )

                Err error ->
                    ( { model | models = demoModels, error = Just ("Failed to fetch models: " ++ httpErrorToString error) }, Cmd.none )

        SelectModel modelId ->
            let
                selected =
                    model.models
                        |> List.filter (\m -> m.id == modelId)
                        |> List.head
            in
            case selected of
                Just selectedModel ->
                    ( { model | selectedModel = selected, outputImage = Nothing, error = Nothing, parameters = [] }
                    , fetchModelSchema selectedModel.id
                    )

                Nothing ->
                    ( model, Cmd.none )

        SchemaFetched modelId result ->
            case result of
                Ok { schema, required, version } ->
                    let
                        params =
                            case Decode.decodeValue (Decode.keyValuePairs Decode.value) schema of
                                Ok properties ->
                                    List.map (parseParameter) properties

                                Err _ ->
                                    [ Parameter "prompt" "" "string" Nothing Nothing Nothing Nothing Nothing Nothing ]
                    in
                    ( { model | parameters = params, requiredFields = required, selectedVersion = version }
                    , Task.attempt ScrollToModel (Dom.getElement "selected-model-section" |> Task.andThen (\info -> Dom.setViewport 0 info.element.y))
                    )

                Err _ ->
                    -- Fallback to default prompt parameter
                    ( { model | parameters = [ Parameter "prompt" "" "string" Nothing Nothing Nothing Nothing Nothing Nothing ], requiredFields = [ "prompt" ], selectedVersion = Nothing }
                    , Task.attempt ScrollToModel (Dom.getElement "selected-model-section" |> Task.andThen (\info -> Dom.setViewport 0 info.element.y))
                    )

        UpdateParameter key value ->
            let
                updatedParams =
                    updateParameterInList key value model.parameters
            in
            ( { model | parameters = updatedParams }, Cmd.none )

        UpdateSearch query ->
            ( { model | searchQuery = query }, Cmd.none )

        GenerateImage ->
            case model.selectedModel of
                Just selectedModel ->
                    ( { model | isGenerating = True, error = Nothing }
                    , generateVideo selectedModel.id model.parameters model.selectedCollection model.selectedVersion
                    )

                Nothing ->
                    ( { model | error = Just "No model selected" }, Cmd.none )

        ImageGenerated result ->
            case result of
                Ok response ->
                    ( { model
                        | isGenerating = False
                        , pollingImageId = Just response.image_id
                        , imageStatus = response.status
                        , error = Nothing
                      }
                    , Task.perform (\_ -> NavigateToImage response.image_id) (Task.succeed ())
                    )

                Err error ->
                    ( { model | isGenerating = False, error = Just (httpErrorToString error) }, Cmd.none )

        NavigateToImage _ ->
            -- This is handled in Main.elm for navigation
            ( model, Cmd.none )

        ScrollToModel _ ->
            ( model, Cmd.none )

        PollImageStatus ->
            ( model, Cmd.none )

        ImageStatusFetched result ->
            case result of
                Ok videoRecord ->
                    ( { model
                        | imageStatus = videoRecord.status
                        , outputImage =
                            if videoRecord.status == "completed" then
                                Just videoRecord.imageUrl
                            else
                                model.outputImage
                        , isGenerating = videoRecord.status /= "completed" && videoRecord.status /= "failed"
                      }
                    , Cmd.none
                    )

                Err error ->
                    ( { model | error = Just (httpErrorToString error) }, Cmd.none )

        FileSelected paramKey file ->
            ( { model | uploadingFile = Just paramKey }
            , uploadImage paramKey file
            )

        ImageUploaded paramKey result ->
            case result of
                Ok imageUrl ->
                    let
                        updatedParams =
                            updateParameterInList paramKey imageUrl model.parameters
                    in
                    ( { model
                        | uploadingFile = Nothing
                        , parameters = updatedParams
                        , error = Nothing
                      }
                    , Cmd.none
                    )

                Err error ->
                    ( { model
                        | uploadingFile = Nothing
                        , error = Just ("Upload failed: " ++ httpErrorToString error)
                      }
                    , Cmd.none
                    )


-- HELPER FUNCTIONS


parseParameter : ( String, Decode.Value ) -> Parameter
parseParameter ( key, value ) =
    let
        paramType =
            Decode.decodeValue (Decode.at [ "type" ] Decode.string) value
                |> Result.withDefault "string"

        enumValues =
            Decode.decodeValue (Decode.at [ "enum" ] (Decode.list Decode.string)) value
                |> Result.toMaybe

        description =
            Decode.decodeValue (Decode.at [ "description" ] Decode.string) value
                |> Result.toMaybe

        default =
            Decode.decodeValue (Decode.field "default" Decode.value) value
                |> Result.toMaybe
                |> Maybe.andThen
                    (\v ->
                        case Decode.decodeValue Decode.string v of
                            Ok s ->
                                Just s

                            Err _ ->
                                case Decode.decodeValue Decode.float v of
                                    Ok f ->
                                        Just (String.fromFloat f)

                                    Err _ ->
                                        case Decode.decodeValue Decode.int v of
                                            Ok i ->
                                                Just (String.fromInt i)

                                            Err _ ->
                                                Nothing
                    )

        minimum =
            Decode.decodeValue (Decode.field "minimum" Decode.float) value
                |> Result.toMaybe

        maximum =
            Decode.decodeValue (Decode.field "maximum" Decode.float) value
                |> Result.toMaybe

        format =
            Decode.decodeValue (Decode.field "format" Decode.string) value
                |> Result.toMaybe

        initialValue =
            Maybe.withDefault "" default
    in
    Parameter key initialValue paramType enumValues description default minimum maximum format


getDefaultParameters : ImageModel -> List Parameter
getDefaultParameters model =
    case model.inputSchema of
        Just schema ->
            case Decode.decodeValue (Decode.keyValuePairs Decode.value) schema of
                Ok properties ->
                    List.map parseParameter properties

                Err _ ->
                    [ Parameter "prompt" "" "string" Nothing Nothing Nothing Nothing Nothing Nothing ]

        Nothing ->
            [ Parameter "prompt" "" "string" Nothing Nothing Nothing Nothing Nothing Nothing ]


updateParameterInList : String -> String -> List Parameter -> List Parameter
updateParameterInList key value params =
    List.map
        (\param ->
            if param.key == key then
                { param | value = value }

            else
                param
        )
        params


-- VIEW


view : Model -> Html Msg
view model =
    div [ class "image-page" ]
        [ h1 [] [ text "Image Models Explorer" ]
        , div [ class "collection-buttons" ]
            [ button
                [ onClick (SelectCollection "text-to-image")
                , class (if model.selectedCollection == "text-to-image" then "collection-button active" else "collection-button")
                ]
                [ text "Text to Image" ]
            , button
                [ onClick (SelectCollection "image-editing")
                , class (if model.selectedCollection == "image-editing" then "collection-button active" else "collection-button")
                ]
                [ text "Image Editing" ]
            , button
                [ onClick (SelectCollection "super-resolution")
                , class (if model.selectedCollection == "super-resolution" then "collection-button active" else "collection-button")
                ]
                [ text "Super Resolution / Upscalers" ]
            ]
        , div [ class "search-section" ]
            [ input
                [ type_ "text"
                , placeholder "Search image models..."
                , value model.searchQuery
                , onInput UpdateSearch
                ]
                []
            , button [ onClick FetchModels, disabled (model.models /= []) ] [ text (if model.models == [] then "Loading..." else "Refresh Models") ]
            ]
        , if List.isEmpty model.models then
            div [ class "loading-text" ] [ text "Loading models..." ]
          else
            div [ class "models-list" ]
                (model.models
                    |> List.filter (\m -> String.contains (String.toLower model.searchQuery) (String.toLower m.name))
                    |> List.map viewModelOption
                )
        , case model.selectedModel of
            Just selected ->
                div [ class "selected-model", id "selected-model-section" ]
                    [ h2 [] [ text selected.name ]
                    , p [] [ text selected.description ]
                    , div [ class "parameters-form-grid" ]
                        (List.map (viewParameter model) model.parameters)
                    , button
                        [ onClick GenerateImage
                        , disabled (hasEmptyRequiredParameters model.parameters model.requiredFields || model.isGenerating)
                        , class "generate-button"
                        ]
                        [ text (if model.isGenerating then "Generating..." else "Generate Image") ]
                    ]

            Nothing ->
                if not (List.isEmpty model.models) then
                    div [] [ text "Select a model from the list above" ]
                else
                    text ""
        , case model.outputImage of
            Just url ->
                div [ class "image-output" ]
                    [ img [ src url, attribute "width" "100%", style "max-width" "800px" ] [] ]

            Nothing ->
                text ""
        , case model.error of
            Just err ->
                div [ class "error" ] [ text err ]

            Nothing ->
                text ""
        ]


viewModelOption : ImageModel -> Html Msg
viewModelOption model =
    div [ class "model-option", onClick (SelectModel model.id) ]
        [ h3 [] [ text model.name ]
        , p [] [ text model.description ]
        ]


viewParameter : Model -> Parameter -> Html Msg
viewParameter model param =
    let
        isDisabled =
            model.isGenerating

        isRequired =
            List.member param.key model.requiredFields

        labelText =
            formatParameterName param.key ++ (if isRequired then " *" else "")

        rangeText =
            case ( param.minimum, param.maximum ) of
                ( Just min, Just max ) ->
                    " (" ++ String.fromFloat min ++ " - " ++ String.fromFloat max ++ ")"

                ( Just min, Nothing ) ->
                    " (min: " ++ String.fromFloat min ++ ")"

                ( Nothing, Just max ) ->
                    " (max: " ++ String.fromFloat max ++ ")"

                ( Nothing, Nothing ) ->
                    ""

        fullDescription =
            case param.description of
                Just desc ->
                    desc ++ rangeText

                Nothing ->
                    if rangeText /= "" then
                        String.trim rangeText

                    else
                        ""

        defaultHint =
            case param.default of
                Just def ->
                    if fullDescription /= "" then
                        fullDescription ++ " (default: " ++ def ++ ")"

                    else
                        "default: " ++ def

                Nothing ->
                    fullDescription

        isImageField =
            param.format == Just "uri" || String.contains "image" (String.toLower param.key)

        isUploading =
            model.uploadingFile == Just param.key
    in
    div [ class "parameter-field" ]
        [ label [ class "parameter-label" ]
            [ text labelText
            , if defaultHint /= "" then
                span [ class "parameter-hint" ] [ text (" — " ++ defaultHint) ]

              else
                text ""
            ]
        , case param.enum of
            Just options ->
                select
                    [ onInput (UpdateParameter param.key)
                    , disabled isDisabled
                    , class "parameter-select"
                    , Html.Attributes.value param.value
                    ]
                    (option [ Html.Attributes.value "" ] [ text "-- Select --" ]
                        :: List.map (\opt -> option [ Html.Attributes.value opt ] [ text opt ]) options
                    )

            Nothing ->
                if isImageField then
                    div [ class "image-upload-container" ]
                        [ input
                            [ type_ "file"
                            , Html.Attributes.accept "image/*"
                            , disabled (isDisabled || isUploading)
                            , class "parameter-file-input"
                            , Html.Attributes.id ("file-" ++ param.key)
                            , on "change" (fileDecoder param.key)
                            ]
                            []
                        , if isUploading then
                            div [ class "upload-status" ] [ text "Uploading..." ]
                          else
                            text ""
                        , input
                            [ type_ "text"
                            , placeholder "Or enter image URL..."
                            , Html.Attributes.value param.value
                            , onInput (UpdateParameter param.key)
                            , disabled (isDisabled || isUploading)
                            , class "parameter-input"
                            ]
                            []
                        ]

                else if param.key == "prompt" then
                    textarea
                        [ placeholder (Maybe.withDefault "Enter prompt..." param.default)
                        , Html.Attributes.value param.value
                        , onInput (UpdateParameter param.key)
                        , disabled isDisabled
                        , class "parameter-input parameter-textarea"
                        ]
                        []

                else if param.paramType == "array" then
                    textarea
                        [ placeholder (Maybe.withDefault "[\"item1\", \"item2\"] or enter single value" param.default)
                        , Html.Attributes.value param.value
                        , onInput (UpdateParameter param.key)
                        , disabled isDisabled
                        , class "parameter-input parameter-textarea"
                        , Html.Attributes.rows 3
                        ]
                        []

                else
                    input
                        [ type_ (if param.paramType == "number" || param.paramType == "integer" then "number" else "text")
                        , placeholder (Maybe.withDefault ("Enter " ++ param.key ++ "...") param.default)
                        , Html.Attributes.value param.value
                        , onInput (UpdateParameter param.key)
                        , disabled isDisabled
                        , class "parameter-input"
                        ]
                        []
        ]


formatParameterName : String -> String
formatParameterName name =
    name
        |> String.split "_"
        |> List.map capitalize
        |> String.join " "


capitalize : String -> String
capitalize str =
    case String.uncons str of
        Just ( first, rest ) ->
            String.fromChar (Char.toUpper first) ++ rest

        Nothing ->
            str


hasEmptyRequiredParameters : List Parameter -> List String -> Bool
hasEmptyRequiredParameters params requiredFields =
    List.any
        (\param ->
            List.member param.key requiredFields && String.isEmpty (String.trim param.value)
        )
        params


fileDecoder : String -> Decode.Decoder Msg
fileDecoder paramKey =
    Decode.at [ "target", "files", "0" ] File.decoder
        |> Decode.map (FileSelected paramKey)


-- HTTP


fetchModels : String -> Cmd Msg
fetchModels collection =
    Http.get
        { url = "/api/image-models?collection=" ++ collection
        , expect = Http.expectJson ModelsFetched (Decode.field "models" (Decode.list videoModelDecoder))
        }


fetchModelSchema : String -> Cmd Msg
fetchModelSchema modelId =
    let
        -- Split modelId into owner/name
        parts =
            String.split "/" modelId

        url =
            case parts of
                [ owner, name ] ->
                    "/api/image-models/" ++ owner ++ "/" ++ name ++ "/schema"

                _ ->
                    ""
    in
    if String.isEmpty url then
        Cmd.none

    else
        Http.get
            { url = url
            , expect = Http.expectJson (SchemaFetched modelId) schemaResponseDecoder
            }


schemaResponseDecoder : Decode.Decoder { schema : Decode.Value, required : List String, version : Maybe String }
schemaResponseDecoder =
    Decode.map3 (\s r v -> { schema = s, required = r, version = v })
        (Decode.field "input_schema" Decode.value)
        (Decode.oneOf
            [ Decode.field "required" (Decode.list Decode.string)
            , Decode.succeed []
            ]
        )
        (Decode.maybe (Decode.field "version" Decode.string))


generateVideo : String -> List Parameter -> String -> Maybe String -> Cmd Msg
generateVideo modelId parameters collection maybeVersion =
    let
        encodeParameterValue : Parameter -> Maybe ( String, Encode.Value )
        encodeParameterValue param =
            if String.isEmpty (String.trim param.value) then
                Nothing
            else
                let
                    encoded =
                        case param.paramType of
                            "integer" ->
                                case String.toInt param.value of
                                    Just i ->
                                        Encode.int i
                                    Nothing ->
                                        Encode.string param.value

                            "number" ->
                                case String.toFloat param.value of
                                    Just f ->
                                        Encode.float f
                                    Nothing ->
                                        Encode.string param.value

                            "boolean" ->
                                case String.toLower param.value of
                                    "true" ->
                                        Encode.bool True
                                    "false" ->
                                        Encode.bool False
                                    _ ->
                                        Encode.string param.value

                            "array" ->
                                -- Try to parse as JSON array, fallback to string
                                case Decode.decodeString (Decode.list Decode.string) param.value of
                                    Ok strings ->
                                        Encode.list Encode.string strings
                                    Err _ ->
                                        -- If not valid JSON array, treat as single-item array
                                        Encode.list Encode.string [ param.value ]

                            _ ->
                                Encode.string param.value
                in
                Just ( param.key, encoded )

        inputObject =
            Encode.object (List.filterMap encodeParameterValue parameters)

        -- Build request object with optional version field
        requestFields =
            [ ( "model_id", Encode.string modelId )
            , ( "input", inputObject )
            , ( "collection", Encode.string collection )
            ]
                ++ (case maybeVersion of
                        Just version ->
                            [ ( "version", Encode.string version ) ]

                        Nothing ->
                            []
                   )
    in
    -- Cookies are sent automatically, no need for Authorization header
    Http.post
        { url = "/api/run-image-model"
        , body = Http.jsonBody (Encode.object requestFields)
        , expect = Http.expectJson ImageGenerated videoResponseDecoder
        }

videoResponseDecoder : Decode.Decoder { image_id : Int, status : String }
videoResponseDecoder =
    Decode.map2 (\id s -> { image_id = id, status = s })
        (Decode.field "image_id" Decode.int)
        (Decode.field "status" Decode.string)


uploadImage : String -> File -> Cmd Msg
uploadImage paramKey file =
    Http.post
        { url = "/api/upload-image"
        , body = Http.multipartBody [ Http.filePart "file" file ]
        , expect = Http.expectJson (ImageUploaded paramKey) uploadResponseDecoder
        }


uploadResponseDecoder : Decode.Decoder String
uploadResponseDecoder =
    Decode.field "url" Decode.string


videoModelDecoder : Decode.Decoder ImageModel
videoModelDecoder =
    Decode.map4 ImageModel
        (Decode.field "id" Decode.string)
        (Decode.field "name" Decode.string)
        (Decode.oneOf
            [ Decode.field "description" Decode.string
            , Decode.succeed "No description available"
            ]
        )
        (Decode.maybe (Decode.field "input_schema" Decode.value))


httpErrorToString : Http.Error -> String
httpErrorToString error =
    case error of
        Http.BadUrl url ->
            "Bad URL: " ++ url

        Http.Timeout ->
            "Request timed out"

        Http.NetworkError ->
            "Network error"

        Http.BadStatus status ->
            "Server error: " ++ String.fromInt status

        Http.BadBody body ->
            "Invalid response: " ++ body


-- Demo models for fallback
demoModels : List ImageModel
demoModels =
    [ ImageModel "demo/text-to-image" "Demo Text-to-Video" "Generates a demo video from text prompt" Nothing
    , ImageModel "demo/image-to-video" "Demo Image-to-Video" "Generates a demo video from image and prompt" Nothing
    ]