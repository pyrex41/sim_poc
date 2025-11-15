module ImageGallery exposing (Model, Msg(..), init, update, view, subscriptions, fetchImages)

import Html exposing (..)
import Html.Attributes exposing (..)
import Html.Events exposing (..)
import Http
import Json.Decode as Decode
import Json.Encode as Encode
import Time


-- MODEL


type alias Model =
    { images : List ImageRecord
    , loading : Bool
    , error : Maybe String
    , selectedImage : Maybe ImageRecord
    , showRawData : Bool
    , videoModels : List VideoModel
    , selectedVideoModel : Maybe String
    , loadingModels : Bool
    }


type alias ImageRecord =
    { id : Int
    , prompt : String
    , imageUrl : String
    , thumbnailUrl : String
    , modelId : String
    , createdAt : String
    , collection : Maybe String
    , parameters : Maybe Decode.Value
    , metadata : Maybe Decode.Value
    , status : String
    }


type alias VideoModel =
    { id : String
    , name : String
    , description : String
    }


init : ( Model, Cmd Msg )
init =
    ( { images = []
      , loading = True
      , error = Nothing
      , selectedImage = Nothing
      , showRawData = False
      , videoModels = []
      , selectedVideoModel = Nothing
      , loadingModels = True
      }
    , Cmd.batch [ fetchImages, fetchVideoModels ]
    )


-- UPDATE


type Msg
    = NoOp
    | FetchImages
    | ImagesFetched (Result Http.Error (List ImageRecord))
    | SelectImage ImageRecord
    | CloseImage
    | ToggleRawData
    | Tick Time.Posix
    | FetchVideoModels
    | VideoModelsFetched (Result Http.Error (List VideoModel))
    | SelectVideoModel String
    | CreateVideoFromImage String String  -- Pass model ID and image URL


update : Msg -> Model -> ( Model, Cmd Msg )
update msg model =
    case msg of
        NoOp ->
            ( model, Cmd.none )

        FetchImages ->
            ( { model | loading = True }, fetchImages )

        ImagesFetched result ->
            case result of
                Ok images ->
                    -- Only update if images actually changed
                    if images == model.images then
                        ( { model | loading = False }, Cmd.none )
                    else
                        ( { model | images = images, loading = False, error = Nothing }, Cmd.none )

                Err error ->
                    -- Don't show 401 errors (authentication issues are handled by login screen)
                    let
                        errorMsg =
                            case error of
                                Http.BadStatus 401 ->
                                    Nothing

                                _ ->
                                    Just (httpErrorToString error)
                    in
                    ( { model | loading = False, error = errorMsg }, Cmd.none )

        SelectImage video ->
            ( { model | selectedImage = Just video, showRawData = False }, Cmd.none )

        CloseImage ->
            ( { model | selectedImage = Nothing, showRawData = False }, Cmd.none )

        ToggleRawData ->
            ( { model | showRawData = not model.showRawData }, Cmd.none )

        Tick _ ->
            -- Don't set loading=True on background refresh to prevent flicker
            ( model, fetchImages )

        FetchVideoModels ->
            ( { model | loadingModels = True }, fetchVideoModels )

        VideoModelsFetched result ->
            case result of
                Ok models ->
                    let
                        -- Auto-select first model if available
                        firstModel =
                            models
                                |> List.head
                                |> Maybe.map .id
                    in
                    ( { model | videoModels = models, loadingModels = False, selectedVideoModel = firstModel }, Cmd.none )

                Err _ ->
                    ( { model | loadingModels = False }, Cmd.none )

        SelectVideoModel modelId ->
            ( { model | selectedVideoModel = Just modelId }, Cmd.none )

        CreateVideoFromImage modelId imageUrl ->
            -- This will be handled by Main.elm to navigate to video page with image and model
            ( model, Cmd.none )


-- VIEW


view : Model -> Html Msg
view model =
    div [ class "image-gallery-page" ]
        [ h1 [] [ text "Generated Images" ]
        , button [ onClick FetchImages, disabled model.loading, class "refresh-button" ]
            [ text (if model.loading then "Loading..." else "Refresh") ]
        , case model.error of
            Just err ->
                div [ class "error" ] [ text err ]

            Nothing ->
                text ""
        , if model.loading && List.isEmpty model.images then
            div [ class "loading-text" ] [ text "Loading images..." ]

          else if List.isEmpty model.images then
            div [ class "empty-state" ] [ text "No images generated yet. Go to the Video Models page to generate some!" ]

          else
            div [ class "images-grid" ]
                (List.map viewImageCard model.images)
        , case model.selectedImage of
            Just video ->
                viewImageModal model video

            Nothing ->
                text ""
        ]


viewImageCard : ImageRecord -> Html Msg
viewImageCard imageRecord =
    let
        errorMessage =
            extractErrorMessage imageRecord
    in
    div [ class "image-card", onClick (SelectImage imageRecord) ]
        [ div [ class "image-thumbnail" ]
            [ if String.isEmpty imageRecord.imageUrl then
                div
                    [ style "width" "100%"
                    , style "height" "100%"
                    , style "display" "flex"
                    , style "flex-direction" "column"
                    , style "align-items" "center"
                    , style "justify-content" "center"
                    , style "background" (if imageRecord.status == "failed" then "#c33" else "#333")
                    , style "color" "#fff"
                    , style "padding" "10px"
                    ]
                    [ div [ style "font-weight" "bold", style "margin-bottom" "5px" ]
                        [ text (String.toUpper imageRecord.status) ]
                    , case errorMessage of
                        Just err ->
                            div [ style "font-size" "12px", style "text-align" "center" ]
                                [ text (truncateString 60 err) ]
                        Nothing ->
                            text ""
                    ]
              else
                img [ src imageRecord.thumbnailUrl, style "width" "100%", style "height" "100%", style "object-fit" "cover" ] []
            ]
        , div [ class "image-card-info" ]
            [ div [ class "image-prompt" ] [ text imageRecord.prompt ]
            , div [ class "image-meta" ]
                [ span [ class "image-model" ] [ text imageRecord.modelId ]
                , span [ class "image-date" ] [ text (formatDate imageRecord.createdAt) ]
                ]
            ]
        ]


viewImageModal : Model -> ImageRecord -> Html Msg
viewImageModal model imageRecord =
    let
        errorMessage =
            extractErrorMessage imageRecord
    in
    div [ class "modal-overlay", onClick CloseImage ]
        [ div [ class "modal-content", onClickNoBubble ]
            [ button [ class "modal-close", onClick CloseImage ] [ text "×" ]
            , h2 [] [ text "Generated Image" ]
            , case errorMessage of
                Just err ->
                    div
                        [ style "background" "#fee"
                        , style "color" "#c33"
                        , style "padding" "15px"
                        , style "border-radius" "4px"
                        , style "margin-bottom" "15px"
                        , style "border" "1px solid #fcc"
                        ]
                        [ strong [] [ text "Error: " ]
                        , text err
                        ]
                Nothing ->
                    text ""
            , if not (String.isEmpty imageRecord.imageUrl) then
                img [ src imageRecord.imageUrl, style "width" "100%", style "max-width" "800px", class "modal-image" ] []
              else
                div
                    [ style "background" "#333"
                    , style "color" "#fff"
                    , style "padding" "40px"
                    , style "text-align" "center"
                    , style "border-radius" "4px"
                    , style "margin-bottom" "15px"
                    ]
                    [ text ("Image " ++ String.toUpper imageRecord.status) ]
            , div [ class "modal-details" ]
                [ div [ class "detail-row" ]
                    [ strong [] [ text "Prompt: " ]
                    , text imageRecord.prompt
                    ]
                , div [ class "detail-row" ]
                    [ strong [] [ text "Model: " ]
                    , text imageRecord.modelId
                    ]
                , case imageRecord.collection of
                    Just coll ->
                        div [ class "detail-row" ]
                            [ strong [] [ text "Collection: " ]
                            , text coll
                            ]

                    Nothing ->
                        text ""
                , div [ class "detail-row" ]
                    [ strong [] [ text "Created: " ]
                    , text imageRecord.createdAt
                    ]
                , div [ class "detail-row" ]
                    [ strong [] [ text "Status: " ]
                    , span
                        [ style "color" (if imageRecord.status == "failed" then "#c33" else "inherit")
                        , style "font-weight" (if imageRecord.status == "failed" then "bold" else "normal")
                        ]
                        [ text imageRecord.status ]
                    ]
                ]
            , if not (String.isEmpty imageRecord.imageUrl) && imageRecord.status == "completed" then
                div [ class "modal-actions", style "margin" "20px 0" ]
                    [ div [ style "margin-bottom" "10px" ]
                        [ strong [] [ text "Select Image-to-Video Model:" ]
                        ]
                    , if model.loadingModels then
                        div [ style "padding" "10px" ] [ text "Loading models..." ]
                      else if List.isEmpty model.videoModels then
                        div [ style "padding" "10px", style "color" "#999" ] [ text "No image-to-video models available" ]
                      else
                        div [ style "margin-bottom" "10px" ]
                            [ select
                                [ onInput SelectVideoModel
                                , style "width" "100%"
                                , style "padding" "8px"
                                , style "border" "1px solid #ccc"
                                , style "border-radius" "4px"
                                , style "font-size" "14px"
                                ]
                                (List.map
                                    (\videoModel ->
                                        option
                                            [ value videoModel.id
                                            , selected (model.selectedVideoModel == Just videoModel.id)
                                            ]
                                            [ text (videoModel.name ++ " - " ++ videoModel.description) ]
                                    )
                                    model.videoModels
                                )
                            ]
                    , case model.selectedVideoModel of
                        Just modelId ->
                            button
                                [ onClick (CreateVideoFromImage modelId imageRecord.imageUrl)
                                , class "create-video-button"
                                , style "background" "#4CAF50"
                                , style "color" "white"
                                , style "padding" "10px 20px"
                                , style "border" "none"
                                , style "border-radius" "4px"
                                , style "cursor" "pointer"
                                , style "font-size" "16px"
                                , style "width" "100%"
                                ]
                                [ text "Create Video from This Image" ]

                        Nothing ->
                            button
                                [ disabled True
                                , class "create-video-button"
                                , style "background" "#ccc"
                                , style "color" "#666"
                                , style "padding" "10px 20px"
                                , style "border" "none"
                                , style "border-radius" "4px"
                                , style "cursor" "not-allowed"
                                , style "font-size" "16px"
                                , style "width" "100%"
                                ]
                                [ text "Select a model first" ]
                    ]
              else
                text ""
            , div [ class "raw-data-section" ]
                [ button [ onClick ToggleRawData, class "toggle-raw-data" ]
                    [ text (if model.showRawData then "▼ Hide Raw Data" else "▶ Show Raw Data") ]
                , if model.showRawData then
                    div [ class "raw-data-content" ]
                        [ viewRawDataField "Parameters" imageRecord.parameters
                        , viewRawDataField "Metadata" imageRecord.metadata
                        ]
                  else
                    text ""
                ]
            ]
        ]


onClickNoBubble : Html.Attribute Msg
onClickNoBubble =
    stopPropagationOn "click" (Decode.succeed ( NoOp, True ))


viewRawDataField : String -> Maybe Decode.Value -> Html Msg
viewRawDataField label maybeValue =
    case maybeValue of
        Just value ->
            div [ class "raw-data-field" ]
                [ h4 [] [ text label ]
                , pre [ class "raw-json" ]
                    [ text (Decode.decodeValue (Decode.value) value
                        |> Result.map (Encode.encode 2)
                        |> Result.withDefault "Invalid JSON")
                    ]
                ]

        Nothing ->
            text ""


formatDate : String -> String
formatDate dateStr =
    -- Simple formatter - just show the date part
    String.left 19 dateStr


extractErrorMessage : ImageRecord -> Maybe String
extractErrorMessage imageRecord =
    -- Try to extract error message from metadata
    case imageRecord.metadata of
        Just metadataValue ->
            Decode.decodeValue (Decode.field "error" Decode.string) metadataValue
                |> Result.toMaybe

        Nothing ->
            Nothing


truncateString : Int -> String -> String
truncateString maxLength str =
    if String.length str <= maxLength then
        str
    else
        String.left (maxLength - 3) str ++ "..."


-- HTTP


fetchImages : Cmd Msg
fetchImages =
    -- Cookies are sent automatically, no need for Authorization header
    Http.get
        { url = "/api/images?limit=50"
        , expect = Http.expectJson ImagesFetched (Decode.field "images" (Decode.list imageDecoder))
        }


fetchVideoModels : Cmd Msg
fetchVideoModels =
    -- Fetch image-to-video models from Replicate
    Http.get
        { url = "/api/video-models?collection=image-to-video"
        , expect = Http.expectJson VideoModelsFetched (Decode.field "models" (Decode.list videoModelDecoder))
        }


videoModelDecoder : Decode.Decoder VideoModel
videoModelDecoder =
    Decode.map3 VideoModel
        (Decode.field "id" Decode.string)
        (Decode.field "name" Decode.string)
        (Decode.field "description" Decode.string)


imageDecoder : Decode.Decoder ImageRecord
imageDecoder =
    Decode.map8
        (\id prompt imageUrl thumbnailUrl modelId createdAt collection parameters ->
            { id = id
            , prompt = prompt
            , imageUrl = imageUrl
            , thumbnailUrl = thumbnailUrl
            , modelId = modelId
            , createdAt = createdAt
            , collection = collection
            , parameters = parameters
            , metadata = Nothing
            , status = "completed"  -- Default, will be overridden below
            }
        )
        (Decode.field "id" Decode.int)
        (Decode.field "prompt" Decode.string)
        (Decode.field "image_url" Decode.string)
        (Decode.field "thumbnail_url" Decode.string)
        (Decode.field "model_id" Decode.string)
        (Decode.field "created_at" Decode.string)
        (Decode.maybe (Decode.field "collection" Decode.string))
        (Decode.maybe (Decode.field "parameters" Decode.value))
        |> Decode.andThen
            (\record ->
                Decode.map2
                    (\status metadata -> { record | status = status, metadata = metadata })
                    (Decode.oneOf
                        [ Decode.field "status" Decode.string
                        , Decode.succeed "completed"
                        ]
                    )
                    (Decode.maybe (Decode.field "metadata" Decode.value))
            )


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


-- SUBSCRIPTIONS


subscriptions : Model -> Sub Msg
subscriptions model =
    Time.every 3000 Tick
