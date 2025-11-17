module VideoDetail exposing (Model, Msg, init, update, view, subscriptions)

import Html exposing (..)
import Html.Attributes exposing (..)
import Http
import Json.Decode as Decode
import Time


-- MODEL


type alias Model =
    { videoId : Int
    , video : Maybe VideoRecord
    , error : Maybe String
    , isPolling : Bool
    }


type alias VideoRecord =
    { id : Int
    , prompt : String
    , videoUrl : String
    , modelId : String
    , createdAt : String
    , status : String
    }


init : Int -> ( Model, Cmd Msg )
init videoId =
    ( { videoId = videoId
      , video = Nothing
      , error = Nothing
      , isPolling = True
      }
    , fetchVideo videoId
    )



-- UPDATE


type Msg
    = VideoFetched (Result Http.Error VideoRecord)
    | PollTick Time.Posix


update : Msg -> Model -> ( Model, Cmd Msg )
update msg model =
    case msg of
        VideoFetched result ->
            case result of
                Ok video ->
                    let
                        -- Stop polling if video is completed or failed
                        shouldStopPolling =
                            video.status == "completed" || video.status == "failed" || video.status == "canceled"
                    in
                    ( { model
                        | video = Just video
                        , error = Nothing
                        , isPolling = not shouldStopPolling
                      }
                    , Cmd.none
                    )

                Err error ->
                    ( { model | error = Just (httpErrorToString error), isPolling = False }
                    , Cmd.none
                    )

        PollTick _ ->
            if model.isPolling then
                ( model, fetchVideo model.videoId )

            else
                ( model, Cmd.none )



-- SUBSCRIPTIONS


subscriptions : Model -> Sub Msg
subscriptions model =
    if model.isPolling then
        Time.every 2000 PollTick

    else
        Sub.none



-- VIEW


view : Model -> Html Msg
view model =
    div [ class "video-detail-page" ]
        [ h1 [] [ text "Video Generation Status" ]
        , case model.error of
            Just err ->
                div [ class "error" ] [ text err ]

            Nothing ->
                text ""
        , case model.video of
            Just video ->
                viewVideoDetail video

            Nothing ->
                div [ class "loading" ] [ text "Loading video information..." ]
        ]


viewVideoDetail : VideoRecord -> Html Msg
viewVideoDetail video =
    div [ class "video-detail" ]
        [ div [ class "video-info" ]
            [ h2 [] [ text "Video Details" ]
            , div [ class "info-row" ]
                [ span [ class "label" ] [ text "Status: " ]
                , span [ class ("status status-" ++ String.toLower video.status) ]
                    [ text (statusText video.status) ]
                ]
            , div [ class "info-row" ]
                [ span [ class "label" ] [ text "Model: " ]
                , span [] [ text video.modelId ]
                ]
            , div [ class "info-row" ]
                [ span [ class "label" ] [ text "Prompt: " ]
                , p [ class "prompt" ] [ text video.prompt ]
                ]
            , div [ class "info-row" ]
                [ span [ class "label" ] [ text "Created: " ]
                , span [] [ text video.createdAt ]
                ]
            ]
        , case video.status of
            "completed" ->
                if String.isEmpty video.videoUrl then
                    div [ class "error" ] [ text "Video completed but no URL available" ]

                else
                    div [ class "video-player" ]
                        [ h3 [] [ text "Generated Video" ]
                        , Html.node "video"
                            [ src video.videoUrl
                            , controls True
                            , attribute "width" "100%"
                            , attribute "style" "max-width: 800px; border-radius: 8px;"
                            ]
                            []
                        , div [ class "video-actions" ]
                            [ a
                                [ href video.videoUrl
                                , download ""
                                , class "download-button"
                                ]
                                [ text "Download Video" ]
                            ]
                        ]

            "processing" ->
                div [ class "processing" ]
                    [ div [ class "spinner" ] []
                    , p [] [ text "Your video is being generated... This may take 30-60 seconds." ]
                    ]

            "failed" ->
                div [ class "error" ]
                    [ text "Video generation failed. Please try again with different parameters." ]

            "canceled" ->
                div [ class "info" ]
                    [ text "Video generation was canceled." ]

            _ ->
                div [ class "info" ]
                    [ text ("Status: " ++ video.status) ]
        ]


statusText : String -> String
statusText status =
    case status of
        "processing" ->
            "⏳ Processing..."

        "completed" ->
            "✅ Completed"

        "failed" ->
            "❌ Failed"

        "canceled" ->
            "🚫 Canceled"

        _ ->
            status



-- HTTP


fetchVideo : Int -> Cmd Msg
fetchVideo videoId =
    Http.get
        { url = "/api/videos/" ++ String.fromInt videoId
        , expect = Http.expectJson VideoFetched videoDecoder
        }


videoDecoder : Decode.Decoder VideoRecord
videoDecoder =
    Decode.map6 VideoRecord
        (Decode.field "id" Decode.int)
        (Decode.field "prompt" Decode.string)
        (Decode.field "video_url" Decode.string)
        (Decode.field "model_id" Decode.string)
        (Decode.field "created_at" Decode.string)
        (Decode.field "status" Decode.string)


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
