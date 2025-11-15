module SimulationGallery exposing (Model, Msg, init, update, view, subscriptions, fetchVideos)

import Dict
import Html exposing (..)
import Html.Attributes exposing (..)
import Html.Events exposing (..)
import Http
import Json.Decode as Decode
import Json.Encode as Encode
import Time


-- MODEL


type alias Model =
    { videos : List GenesisVideoRecord
    , loading : Bool
    , error : Maybe String
    , selectedVideo : Maybe GenesisVideoRecord
    , showRawData : Bool
    , token : Maybe String
    }


type alias GenesisVideoRecord =
    { id : Int
    , videoPath : String
    , quality : String
    , duration : Float
    , fps : Int
    , resolution : String
    , sceneContext : Maybe String
    , objectDescriptions : Maybe Decode.Value
    , createdAt : String
    , status : String
    , metadata : Maybe Decode.Value
    }


init : Maybe String -> ( Model, Cmd Msg )
init token =
    ( { videos = []
      , loading = True
      , error = Nothing
      , selectedVideo = Nothing
      , showRawData = False
      , token = token
      }
    , fetchVideos token
    )


-- UPDATE


type Msg
    = NoOp
    | FetchVideos
    | VideosFetched (Result Http.Error (List GenesisVideoRecord))
    | SelectVideo GenesisVideoRecord
    | CloseVideo
    | ToggleRawData
    | Tick Time.Posix


update : Msg -> Model -> ( Model, Cmd Msg )
update msg model =
    case msg of
        NoOp ->
            ( model, Cmd.none )

        FetchVideos ->
            ( { model | loading = True }, fetchVideos model.token )

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
            ( { model | loading = True }, fetchVideos model.token )


-- VIEW


view : Model -> Html Msg
view model =
    div [ class "video-gallery-page simulation-gallery-page" ]
        [ h1 [] [ text "Genesis Simulation Gallery" ]
        , div [ class "gallery-header" ]
            [ p [ class "gallery-description" ]
                [ text "Photorealistic simulations rendered with Genesis physics engine and LLM semantic augmentation" ]
            , button [ onClick FetchVideos, disabled model.loading, class "refresh-button" ]
                [ text (if model.loading then "Loading..." else "Refresh") ]
            ]
        , case model.error of
            Just err ->
                div [ class "error" ] [ text err ]

            Nothing ->
                text ""
        , if model.loading && List.isEmpty model.videos then
            div [ class "loading-text" ] [ text "Loading simulations..." ]

          else if List.isEmpty model.videos then
            div [ class "empty-state" ]
                [ text "No simulations generated yet. Create a scene in the editor and click 'Render with Genesis' to generate your first photorealistic simulation!" ]

          else
            div [ class "videos-grid" ]
                (List.map viewVideoCard model.videos)
        , case model.selectedVideo of
            Just video ->
                viewVideoModal model video

            Nothing ->
                text ""
        ]


viewVideoCard : GenesisVideoRecord -> Html Msg
viewVideoCard videoRecord =
    div [ class "video-card simulation-card", onClick (SelectVideo videoRecord) ]
        [ div [ class "video-thumbnail" ]
            [ video [ src (videoUrlFromPath videoRecord.videoPath), attribute "preload" "metadata" ] [] ]
        , div [ class "video-card-info" ]
            [ div [ class "video-prompt" ]
                [ case videoRecord.sceneContext of
                    Just context ->
                        text context

                    Nothing ->
                        text ("Genesis Simulation #" ++ String.fromInt videoRecord.id)
                ]
            , div [ class "video-meta" ]
                [ span [ class "video-quality" ]
                    [ text (String.toUpper videoRecord.quality ++ " quality") ]
                , span [ class "video-duration" ]
                    [ text (String.fromFloat videoRecord.duration ++ "s @ " ++ String.fromInt videoRecord.fps ++ "fps") ]
                , span [ class "video-resolution" ]
                    [ text videoRecord.resolution ]
                , span [ class "video-date" ]
                    [ text (formatDate videoRecord.createdAt) ]
                ]
            ]
        ]


viewVideoModal : Model -> GenesisVideoRecord -> Html Msg
viewVideoModal model videoRecord =
    div [ class "modal-overlay", onClick CloseVideo ]
        [ div [ class "modal-content simulation-modal", onClickNoBubble ]
            [ button [ class "modal-close", onClick CloseVideo ] [ text "×" ]
            , h2 [] [ text "Genesis Simulation" ]
            , video [ src (videoUrlFromPath videoRecord.videoPath), controls True, attribute "width" "100%", class "modal-video", attribute "loop" "true" ] []
            , div [ class "modal-details" ]
                [ case videoRecord.sceneContext of
                    Just context ->
                        div [ class "detail-row" ]
                            [ strong [] [ text "Scene Context: " ]
                            , text context
                            ]

                    Nothing ->
                        text ""
                , div [ class "detail-row" ]
                    [ strong [] [ text "Quality: " ]
                    , text (String.toUpper videoRecord.quality)
                    ]
                , div [ class "detail-row" ]
                    [ strong [] [ text "Duration: " ]
                    , text (String.fromFloat videoRecord.duration ++ " seconds @ " ++ String.fromInt videoRecord.fps ++ " fps")
                    ]
                , div [ class "detail-row" ]
                    [ strong [] [ text "Resolution: " ]
                    , text videoRecord.resolution
                    ]
                , div [ class "detail-row" ]
                    [ strong [] [ text "Created: " ]
                    , text videoRecord.createdAt
                    ]
                , div [ class "detail-row" ]
                    [ strong [] [ text "Status: " ]
                    , text videoRecord.status
                    ]
                , case videoRecord.objectDescriptions of
                    Just descriptions ->
                        div [ class "detail-row object-descriptions" ]
                            [ strong [] [ text "Object Descriptions:" ]
                            , viewObjectDescriptions descriptions
                            ]

                    Nothing ->
                        text ""
                ]
            , div [ class "raw-data-section" ]
                [ button [ onClick ToggleRawData, class "toggle-raw-data" ]
                    [ text (if model.showRawData then "▼ Hide Raw Data" else "▶ Show Raw Data") ]
                , if model.showRawData then
                    div [ class "raw-data-content" ]
                        [ viewRawDataField "Object Descriptions" videoRecord.objectDescriptions
                        , viewRawDataField "Metadata" videoRecord.metadata
                        ]
                  else
                    text ""
                ]
            ]
        ]


viewObjectDescriptions : Decode.Value -> Html Msg
viewObjectDescriptions descriptionsValue =
    case Decode.decodeValue (Decode.dict Decode.string) descriptionsValue of
        Ok descriptions ->
            ul [ class "object-descriptions-list" ]
                (List.map
                    (\( objId, desc ) ->
                        li []
                            [ strong [] [ text (objId ++ ": ") ]
                            , text desc
                            ]
                    )
                    (Dict.toList descriptions)
                )

        Err _ ->
            pre [ class "raw-json" ]
                [ text (Encode.encode 2 descriptionsValue) ]


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
                    [ text (Encode.encode 2 value) ]
                ]

        Nothing ->
            text ""


formatDate : String -> String
formatDate dateStr =
    -- Simple formatter - just show the date part
    String.left 19 dateStr


videoUrlFromPath : String -> String
videoUrlFromPath path =
    -- Convert backend path to URL
    String.replace "backend/DATA/" "/data/" path


-- HTTP


fetchVideos : Maybe String -> Cmd Msg
fetchVideos maybeToken =
    let
        headers =
            case maybeToken of
                Just token ->
                    [ Http.header "Authorization" ("Bearer " ++ token) ]

                Nothing ->
                    []
    in
    Http.request
        { method = "GET"
        , headers = headers
        , url = "/api/genesis/videos?limit=50"
        , body = Http.emptyBody
        , expect = Http.expectJson VideosFetched (Decode.field "videos" (Decode.list videoDecoder))
        , timeout = Nothing
        , tracker = Nothing
        }


videoDecoder : Decode.Decoder GenesisVideoRecord
videoDecoder =
    Decode.map8
        (\id videoPath quality duration fps resolution sceneContext objectDescriptions ->
            { id = id
            , videoPath = videoPath
            , quality = quality
            , duration = duration
            , fps = fps
            , resolution = resolution
            , sceneContext = sceneContext
            , objectDescriptions = objectDescriptions
            , createdAt = ""
            , status = "completed"
            , metadata = Nothing
            }
        )
        (Decode.field "id" Decode.int)
        (Decode.field "video_path" Decode.string)
        (Decode.field "quality" Decode.string)
        (Decode.field "duration" Decode.float)
        (Decode.field "fps" Decode.int)
        (Decode.field "resolution" Decode.string)
        (Decode.maybe (Decode.field "scene_context" Decode.string))
        (Decode.maybe (Decode.field "object_descriptions" Decode.value))
        |> Decode.andThen
            (\record ->
                Decode.map2
                    (\createdAt status ->
                        { record | createdAt = createdAt, status = status }
                    )
                    (Decode.field "created_at" Decode.string)
                    (Decode.field "status" Decode.string)
            )
        |> Decode.andThen
            (\record ->
                Decode.map
                    (\metadata ->
                        { record | metadata = metadata }
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

        Http.BadStatus code ->
            "Server error: " ++ String.fromInt code

        Http.BadBody message ->
            "Invalid response: " ++ message


-- SUBSCRIPTIONS


subscriptions : Model -> Sub Msg
subscriptions model =
    -- Auto-refresh every 30 seconds
    Time.every 30000 Tick
