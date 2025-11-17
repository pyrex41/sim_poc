module VideoGallery exposing (Model, Msg, init, update, view, subscriptions)

import Html exposing (..)
import Html.Attributes exposing (..)
import Html.Events exposing (..)
import Http
import Json.Decode as Decode
import Json.Encode as Encode
import Time


-- MODEL


type alias Model =
    { videos : List VideoRecord
    , loading : Bool
    , error : Maybe String
    , selectedVideo : Maybe VideoRecord
    , showRawData : Bool
    }


type alias VideoRecord =
    { id : Int
    , prompt : String
    , videoUrl : String
    , modelId : String
    , createdAt : String
    , collection : Maybe String
    , parameters : Maybe Decode.Value
    , metadata : Maybe Decode.Value
    , status : String
    }


init : ( Model, Cmd Msg )
init =
    ( { videos = []
      , loading = True
      , error = Nothing
      , selectedVideo = Nothing
      , showRawData = False
      }
    , fetchVideos
    )


-- UPDATE


type Msg
    = NoOp
    | FetchVideos
    | VideosFetched (Result Http.Error (List VideoRecord))
    | SelectVideo VideoRecord
    | CloseVideo
    | ToggleRawData
    | Tick Time.Posix


update : Msg -> Model -> ( Model, Cmd Msg )
update msg model =
    case msg of
        NoOp ->
            ( model, Cmd.none )

        FetchVideos ->
            ( { model | loading = True }, fetchVideos )

        VideosFetched result ->
            case result of
                Ok videos ->
                    ( { model | videos = videos, loading = False, error = Nothing }, Cmd.none )

                Err error ->
                    ( { model | loading = False, error = Just (httpErrorToString error) }, Cmd.none )

        SelectVideo video ->
            ( { model | selectedVideo = Just video, showRawData = False }, Cmd.none )

        CloseVideo ->
            ( { model | selectedVideo = Nothing, showRawData = False }, Cmd.none )

        ToggleRawData ->
            ( { model | showRawData = not model.showRawData }, Cmd.none )

        Tick _ ->
            ( { model | loading = True }, fetchVideos )


-- VIEW


view : Model -> Html Msg
view model =
    div [ class "video-gallery-page" ]
        [ h1 [] [ text "Generated Videos" ]
        , button [ onClick FetchVideos, disabled model.loading, class "refresh-button" ]
            [ text (if model.loading then "Loading..." else "Refresh") ]
        , case model.error of
            Just err ->
                div [ class "error" ] [ text err ]

            Nothing ->
                text ""
        , if model.loading && List.isEmpty model.videos then
            div [ class "loading-text" ] [ text "Loading videos..." ]

          else if List.isEmpty model.videos then
            div [ class "empty-state" ] [ text "No videos generated yet. Go to the Video Models page to generate some!" ]

          else
            div [ class "videos-grid" ]
                (List.map viewVideoCard model.videos)
        , case model.selectedVideo of
            Just video ->
                viewVideoModal model video

            Nothing ->
                text ""
        ]


viewVideoCard : VideoRecord -> Html Msg
viewVideoCard videoRecord =
    div [ class "video-card", onClick (SelectVideo videoRecord) ]
        [ div [ class "video-thumbnail" ]
            [ video [ src videoRecord.videoUrl, attribute "preload" "metadata" ] [] ]
        , div [ class "video-card-info" ]
            [ div [ class "video-prompt" ] [ text videoRecord.prompt ]
            , div [ class "video-meta" ]
                [ span [ class "video-model" ] [ text videoRecord.modelId ]
                , span [ class "video-date" ] [ text (formatDate videoRecord.createdAt) ]
                ]
            ]
        ]


viewVideoModal : Model -> VideoRecord -> Html Msg
viewVideoModal model videoRecord =
    div [ class "modal-overlay", onClick CloseVideo ]
        [ div [ class "modal-content", onClickNoBubble ]
            [ button [ class "modal-close", onClick CloseVideo ] [ text "×" ]
            , h2 [] [ text "Generated Video" ]
            , video [ src videoRecord.videoUrl, controls True, attribute "width" "100%", class "modal-video" ] []
            , div [ class "modal-details" ]
                [ div [ class "detail-row" ]
                    [ strong [] [ text "Prompt: " ]
                    , text videoRecord.prompt
                    ]
                , div [ class "detail-row" ]
                    [ strong [] [ text "Model: " ]
                    , text videoRecord.modelId
                    ]
                , case videoRecord.collection of
                    Just coll ->
                        div [ class "detail-row" ]
                            [ strong [] [ text "Collection: " ]
                            , text coll
                            ]

                    Nothing ->
                        text ""
                , div [ class "detail-row" ]
                    [ strong [] [ text "Created: " ]
                    , text videoRecord.createdAt
                    ]
                , div [ class "detail-row" ]
                    [ strong [] [ text "Status: " ]
                    , text videoRecord.status
                    ]
                ]
            , div [ class "raw-data-section" ]
                [ button [ onClick ToggleRawData, class "toggle-raw-data" ]
                    [ text (if model.showRawData then "▼ Hide Raw Data" else "▶ Show Raw Data") ]
                , if model.showRawData then
                    div [ class "raw-data-content" ]
                        [ viewRawDataField "Parameters" videoRecord.parameters
                        , viewRawDataField "Metadata" videoRecord.metadata
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


-- HTTP


fetchVideos : Cmd Msg
fetchVideos =
    Http.get
        { url = "/api/videos?limit=50"
        , expect = Http.expectJson VideosFetched (Decode.field "videos" (Decode.list videoDecoder))
        }


videoDecoder : Decode.Decoder VideoRecord
videoDecoder =
    Decode.map8
        (\id prompt videoUrl modelId createdAt collection parameters metadata ->
            { id = id
            , prompt = prompt
            , videoUrl = videoUrl
            , modelId = modelId
            , createdAt = createdAt
            , collection = collection
            , parameters = parameters
            , metadata = metadata
            , status = "completed"  -- Default status
            }
        )
        (Decode.field "id" Decode.int)
        (Decode.field "prompt" Decode.string)
        (Decode.field "video_url" Decode.string)
        (Decode.field "model_id" Decode.string)
        (Decode.field "created_at" Decode.string)
        (Decode.maybe (Decode.field "collection" Decode.string))
        (Decode.maybe (Decode.field "parameters" Decode.value))
        (Decode.maybe (Decode.field "metadata" Decode.value))


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
