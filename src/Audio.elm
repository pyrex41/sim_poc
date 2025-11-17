module Audio exposing (Model, Msg(..), init, update, view)

import Browser.Dom as Dom
import Html exposing (..)
import Html.Attributes exposing (..)
import Html.Events exposing (..)
import Http
import Json.Decode as Decode
import Json.Encode as Encode
import Task


-- MODEL


type alias Model =
    { models : List AudioModel
    , selectedModel : Maybe AudioModel
    , parameters : List Parameter
    , isGenerating : Bool
    , outputAudio : Maybe String
    , error : Maybe String
    , searchQuery : String
    , selectedCollection : String
    , requiredFields : List String
    , pollingAudioId : Maybe Int
    , audioStatus : String
    , selectedVersion : Maybe String
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


type alias AudioModel =
    { id : String
    , name : String
    , description : String
    , inputSchema : Maybe Decode.Value
    }


type alias AudioRecord =
    { id : Int
    , prompt : String
    , audioUrl : String
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
      , outputAudio = Nothing
      , error = Nothing
      , searchQuery = ""
      , selectedCollection = "text-to-audio"
      , requiredFields = []
      , pollingAudioId = Nothing
      , audioStatus = ""
      , selectedVersion = Nothing
      }
    , fetchModels "text-to-audio"
    )


-- UPDATE


type Msg
    = NoOp
    | FetchModels
    | SelectCollection String
    | ModelsFetched (Result Http.Error (List AudioModel))
    | SelectModel String
    | SchemaFetched String (Result Http.Error { schema : Decode.Value, required : List String, version : Maybe String })
    | UpdateParameter String String
    | UpdateSearch String
    | GenerateAudio
    | AudioGenerated (Result Http.Error { audio_id : Int, status : String })
    | NavigateToAudio Int
    | PollAudioStatus
    | AudioStatusFetched (Result Http.Error AudioRecord)
    | ScrollToModel (Result Dom.Error ())


update : Msg -> Model -> ( Model, Cmd Msg )
update msg model =
    case msg of
        NoOp ->
            ( model, Cmd.none )

        FetchModels ->
            ( model, fetchModels model.selectedCollection )

        SelectCollection collection ->
            ( { model | selectedCollection = collection, selectedModel = Nothing, outputAudio = Nothing, requiredFields = [], selectedVersion = Nothing }
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
                    ( { model | selectedModel = selected, outputAudio = Nothing, error = Nothing, parameters = [] }
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

        GenerateAudio ->
            case model.selectedModel of
                Just selectedModel ->
                    ( { model | isGenerating = True, error = Nothing }
                    , generateAudio selectedModel.id model.parameters model.selectedCollection model.selectedVersion
                    )

                Nothing ->
                    ( { model | error = Just "No model selected" }, Cmd.none )

        AudioGenerated result ->
            case result of
                Ok response ->
                    ( { model
                        | isGenerating = False
                        , pollingAudioId = Just response.audio_id
                        , audioStatus = response.status
                        , error = Nothing
                      }
                    , Task.perform (\_ -> NavigateToAudio response.audio_id) (Task.succeed ())
                    )

                Err error ->
                    ( { model | isGenerating = False, error = Just (httpErrorToString error) }, Cmd.none )

        NavigateToAudio _ ->
            -- This is handled in Main.elm for navigation
            ( model, Cmd.none )

        ScrollToModel _ ->
            ( model, Cmd.none )

        PollAudioStatus ->
            ( model, Cmd.none )

        AudioStatusFetched result ->
            case result of
                Ok audioRecord ->
                    ( { model
                        | audioStatus = audioRecord.status
                        , outputAudio =
                            if audioRecord.status == "completed" then
                                Just audioRecord.audioUrl
                            else
                                model.outputAudio
                        , isGenerating = audioRecord.status /= "completed" && audioRecord.status /= "failed"
                      }
                    , Cmd.none
                    )

                Err error ->
                    ( { model | error = Just (httpErrorToString error) }, Cmd.none )


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


getDefaultParameters : AudioModel -> List Parameter
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
    div [ class "audio-page" ]
        [ h1 [] [ text "Audio Models Explorer" ]
        , div [ class "search-section" ]
            [ input
                [ type_ "text"
                , placeholder "Search audio models..."
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
                        [ onClick GenerateAudio
                        , disabled (hasEmptyRequiredParameters model.parameters model.requiredFields || model.isGenerating)
                        , class "generate-button"
                        ]
                        [ text (if model.isGenerating then "Generating..." else "Generate Audio") ]
                    ]

            Nothing ->
                if not (List.isEmpty model.models) then
                    div [] [ text "Select a model from the list above" ]
                else
                    text ""
        , case model.outputAudio of
            Just url ->
                div [ class "audio-output" ]
                    [ Html.node "audio" [ src url, controls True, attribute "style" "width: 100%; max-width: 600px;" ] [] ]

            Nothing ->
                text ""
        , case model.error of
            Just err ->
                div [ class "error" ] [ text err ]

            Nothing ->
                text ""
        ]


viewModelOption : AudioModel -> Html Msg
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
                if param.key == "prompt" then
                    textarea
                        [ placeholder (Maybe.withDefault "Enter prompt..." param.default)
                        , Html.Attributes.value param.value
                        , onInput (UpdateParameter param.key)
                        , disabled isDisabled
                        , class "parameter-input parameter-textarea"
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


-- HTTP


fetchModels : String -> Cmd Msg
fetchModels collection =
    Http.get
        { url = "/api/audio-models?collection=" ++ collection
        , expect = Http.expectJson ModelsFetched (Decode.field "models" (Decode.list audioModelDecoder))
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
                    "/api/audio-models/" ++ owner ++ "/" ++ name ++ "/schema"

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


generateAudio : String -> List Parameter -> String -> Maybe String -> Cmd Msg
generateAudio modelId parameters collection maybeVersion =
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
        { url = "/api/v2/generate/audio"
        , body = Http.jsonBody (Encode.object requestFields)
        , expect = Http.expectJson AudioGenerated audioResponseDecoder
        }

audioResponseDecoder : Decode.Decoder { audio_id : Int, status : String }
audioResponseDecoder =
    Decode.map2 (\id s -> { audio_id = id, status = s })
        (Decode.field "audio_id" Decode.int)
        (Decode.field "status" Decode.string)


audioModelDecoder : Decode.Decoder AudioModel
audioModelDecoder =
    Decode.map4 AudioModel
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
demoModels : List AudioModel
demoModels =
    [ AudioModel "meta/musicgen" "MusicGen" "Generate music from text prompts" Nothing
    , AudioModel "riffusion/riffusion" "Riffusion" "Generate music using Riffusion" Nothing
    ]
