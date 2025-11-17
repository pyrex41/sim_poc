module AudioDetail exposing (Model, Msg, init, update, view, subscriptions)

import Html exposing (..)
import Html.Attributes exposing (..)
import Http
import Json.Decode as Decode
import Time


-- MODEL


type alias Model =
    { audioId : Int
    , audio : Maybe AudioRecord
    , error : Maybe String
    , isPolling : Bool
    }


type alias AudioRecord =
    { id : Int
    , prompt : String
    , audioUrl : String
    , modelId : String
    , createdAt : String
    , status : String
    , metadata : Maybe Decode.Value
    , duration : Maybe Float
    }


init : Int -> ( Model, Cmd Msg )
init audioId =
    ( { audioId = audioId
      , audio = Nothing
      , error = Nothing
      , isPolling = True
      }
    , fetchAudio audioId
    )



-- UPDATE


type Msg
    = AudioFetched (Result Http.Error AudioRecord)
    | PollTick Time.Posix


update : Msg -> Model -> ( Model, Cmd Msg )
update msg model =
    case msg of
        AudioFetched result ->
            case result of
                Ok audio ->
                    let
                        -- Stop polling if audio is completed or failed
                        shouldStopPolling =
                            audio.status == "completed" || audio.status == "failed" || audio.status == "canceled"
                    in
                    ( { model
                        | audio = Just audio
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
                ( model, fetchAudio model.audioId )

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
    div [ class "audio-detail-page" ]
        [ h1 [] [ text "Audio Generation Status" ]
        , case model.error of
            Just err ->
                div [ class "error" ] [ text err ]

            Nothing ->
                text ""
        , case model.audio of
            Just audio ->
                viewAudioDetail audio

            Nothing ->
                div [ class "loading" ] [ text "Loading audio information..." ]
        ]


viewAudioDetail : AudioRecord -> Html Msg
viewAudioDetail audio =
    div [ class "audio-detail" ]
        [ div [ class "audio-info" ]
            [ h2 [] [ text "Audio Details" ]
            , div [ class "info-row" ]
                [ span [ class "label" ] [ text "Status: " ]
                , span [ class ("status status-" ++ String.toLower audio.status) ]
                    [ text (statusText audio.status) ]
                ]
            , div [ class "info-row" ]
                [ span [ class "label" ] [ text "Model: " ]
                , span [] [ text audio.modelId ]
                ]
            , div [ class "info-row" ]
                [ span [ class "label" ] [ text "Prompt: " ]
                , p [ class "prompt" ] [ text audio.prompt ]
                ]
            , case audio.duration of
                Just dur ->
                    div [ class "info-row" ]
                        [ span [ class "label" ] [ text "Duration: " ]
                        , span [] [ text (formatDuration dur) ]
                        ]

                Nothing ->
                    text ""
            , div [ class "info-row" ]
                [ span [ class "label" ] [ text "Created: " ]
                , span [] [ text audio.createdAt ]
                ]
            ]
        , case audio.status of
            "completed" ->
                if String.isEmpty audio.audioUrl then
                    div [ class "error" ] [ text "Audio completed but no URL available" ]

                else
                    div [ class "audio-viewer" ]
                        [ h3 [] [ text "Generated Audio" ]
                        , Html.node "audio"
                            [ src audio.audioUrl
                            , controls True
                            , attribute "style" "width: 100%; max-width: 600px;"
                            ]
                            []
                        , div [ class "audio-actions" ]
                            [ a
                                [ href audio.audioUrl
                                , download ""
                                , class "download-button"
                                ]
                                [ text "Download Audio" ]
                            ]
                        ]

            "processing" ->
                div [ class "processing" ]
                    [ div [ class "spinner" ] []
                    , p [] [ text "Your audio is being generated... This may take 30-60 seconds." ]
                    ]

            "failed" ->
                div [ class "error" ]
                    [ text (case extractErrorMessage audio of
                        Just errorMsg ->
                            "Audio generation failed: " ++ errorMsg

                        Nothing ->
                            "Audio generation failed. Please try again with different parameters."
                    ) ]

            "canceled" ->
                div [ class "info" ]
                    [ text "Audio generation was canceled." ]

            _ ->
                div [ class "info" ]
                    [ text ("Status: " ++ audio.status) ]
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


formatDuration : Float -> String
formatDuration seconds =
    let
        mins = floor (seconds / 60)
        secs = floor seconds - (mins * 60)
        secsStr = if secs < 10 then "0" ++ String.fromInt secs else String.fromInt secs
    in
    String.fromInt mins ++ ":" ++ secsStr


extractErrorMessage : AudioRecord -> Maybe String
extractErrorMessage audioRecord =
    -- Try to extract error message from metadata
    case audioRecord.metadata of
        Just metadataValue ->
            Decode.decodeValue (Decode.field "error" Decode.string) metadataValue
                |> Result.toMaybe

        Nothing ->
            Nothing



-- HTTP


fetchAudio : Int -> Cmd Msg
fetchAudio audioId =
    Http.get
        { url = "/api/audio/" ++ String.fromInt audioId
        , expect = Http.expectJson AudioFetched audioDecoder
        }


audioDecoder : Decode.Decoder AudioRecord
audioDecoder =
    Decode.map8 AudioRecord
        (Decode.field "id" Decode.int)
        (Decode.field "prompt" Decode.string)
        (Decode.field "audio_url" Decode.string)
        (Decode.field "model_id" Decode.string)
        (Decode.field "created_at" Decode.string)
        (Decode.field "status" Decode.string)
        (Decode.maybe (Decode.field "metadata" Decode.value))
        (Decode.maybe (Decode.field "duration" Decode.float))


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
