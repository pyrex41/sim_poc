module AudioGallery exposing (Model, Msg(..), init, update, view, subscriptions, fetchAudio)

import Html exposing (..)
import Html.Attributes exposing (..)
import Html.Events exposing (..)
import Http
import Json.Decode as Decode
import Json.Encode as Encode
import Time


-- MODEL


type alias Model =
    { audio : List AudioRecord
    , loading : Bool
    , error : Maybe String
    , selectedAudio : Maybe AudioRecord
    , showRawData : Bool
    }


type alias AudioRecord =
    { id : Int
    , prompt : String
    , audioUrl : String
    , modelId : String
    , createdAt : String
    , collection : Maybe String
    , parameters : Maybe Decode.Value
    , metadata : Maybe Decode.Value
    , status : String
    , duration : Maybe Float
    }


init : ( Model, Cmd Msg )
init =
    ( { audio = []
      , loading = True
      , error = Nothing
      , selectedAudio = Nothing
      , showRawData = False
      }
    , fetchAudio
    )


-- UPDATE


type Msg
    = NoOp
    | FetchAudio
    | AudioFetched (Result Http.Error (List AudioRecord))
    | SelectAudio AudioRecord
    | CloseAudio
    | ToggleRawData
    | Tick Time.Posix


update : Msg -> Model -> ( Model, Cmd Msg )
update msg model =
    case msg of
        NoOp ->
            ( model, Cmd.none )

        FetchAudio ->
            ( { model | loading = True }, fetchAudio )

        AudioFetched result ->
            case result of
                Ok audio ->
                    -- Only update if audio actually changed
                    if audio == model.audio then
                        ( { model | loading = False }, Cmd.none )
                    else
                        ( { model | audio = audio, loading = False, error = Nothing }, Cmd.none )

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

        SelectAudio audio ->
            ( { model | selectedAudio = Just audio, showRawData = False }, Cmd.none )

        CloseAudio ->
            ( { model | selectedAudio = Nothing, showRawData = False }, Cmd.none )

        ToggleRawData ->
            ( { model | showRawData = not model.showRawData }, Cmd.none )

        Tick _ ->
            -- Don't set loading=True on background refresh to prevent flicker
            ( model, fetchAudio )


-- VIEW


view : Model -> Html Msg
view model =
    div [ class "audio-gallery-page" ]
        [ h1 [] [ text "Generated Audio" ]
        , button [ onClick FetchAudio, disabled model.loading, class "refresh-button" ]
            [ text (if model.loading then "Loading..." else "Refresh") ]
        , case model.error of
            Just err ->
                div [ class "error" ] [ text err ]

            Nothing ->
                text ""
        , if model.loading && List.isEmpty model.audio then
            div [ class "loading-text" ] [ text "Loading audio..." ]

          else if List.isEmpty model.audio then
            div [ class "empty-state" ] [ text "No audio generated yet. Go to the Audio Models page to generate some!" ]

          else
            div [ class "audio-grid" ]
                (List.map viewAudioCard model.audio)
        , case model.selectedAudio of
            Just audio ->
                viewAudioModal model audio

            Nothing ->
                text ""
        ]


viewAudioCard : AudioRecord -> Html Msg
viewAudioCard audioRecord =
    let
        errorMessage =
            extractErrorMessage audioRecord
    in
    div [ class "audio-card", onClick (SelectAudio audioRecord) ]
        [ div [ class "audio-thumbnail" ]
            [ if String.isEmpty audioRecord.audioUrl then
                div
                    [ style "width" "100%"
                    , style "height" "100%"
                    , style "display" "flex"
                    , style "flex-direction" "column"
                    , style "align-items" "center"
                    , style "justify-content" "center"
                    , style "background" (if audioRecord.status == "failed" then "#c33" else "#333")
                    , style "color" "#fff"
                    , style "padding" "10px"
                    ]
                    [ div [ style "font-weight" "bold", style "margin-bottom" "5px" ]
                        [ text (String.toUpper audioRecord.status) ]
                    , case errorMessage of
                        Just err ->
                            div [ style "font-size" "12px", style "text-align" "center" ]
                                [ text (truncateString 60 err) ]
                        Nothing ->
                            text ""
                    ]
              else
                div
                    [ style "width" "100%"
                    , style "height" "100%"
                    , style "display" "flex"
                    , style "flex-direction" "column"
                    , style "align-items" "center"
                    , style "justify-content" "center"
                    , style "background" "linear-gradient(135deg, #667eea 0%, #764ba2 100%)"
                    , style "color" "#fff"
                    , style "padding" "20px"
                    ]
                    [ div [ style "font-size" "48px", style "margin-bottom" "10px" ] [ text "♪" ]
                    , case audioRecord.duration of
                        Just dur ->
                            div [ style "font-size" "14px" ] [ text (formatDuration dur) ]
                        Nothing ->
                            text ""
                    ]
            ]
        , div [ class "audio-card-info" ]
            [ div [ class "audio-prompt" ] [ text audioRecord.prompt ]
            , div [ class "audio-meta" ]
                [ span [ class "audio-model" ] [ text audioRecord.modelId ]
                , span [ class "audio-date" ] [ text (formatDate audioRecord.createdAt) ]
                ]
            ]
        ]


viewAudioModal : Model -> AudioRecord -> Html Msg
viewAudioModal model audioRecord =
    let
        errorMessage =
            extractErrorMessage audioRecord
    in
    div [ class "modal-overlay", onClick CloseAudio ]
        [ div [ class "modal-content", onClickNoBubble ]
            [ button [ class "modal-close", onClick CloseAudio ] [ text "×" ]
            , h2 [] [ text "Generated Audio" ]
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
            , if not (String.isEmpty audioRecord.audioUrl) then
                div [ style "margin-bottom" "20px" ]
                    [ Html.node "audio"
                        [ src audioRecord.audioUrl
                        , controls True
                        , attribute "style" "width: 100%; max-width: 600px;"
                        , class "modal-audio"
                        ]
                        []
                    ]
              else
                div
                    [ style "background" "#333"
                    , style "color" "#fff"
                    , style "padding" "40px"
                    , style "text-align" "center"
                    , style "border-radius" "4px"
                    , style "margin-bottom" "15px"
                    ]
                    [ text ("Audio " ++ String.toUpper audioRecord.status) ]
            , div [ class "modal-details" ]
                [ div [ class "detail-row" ]
                    [ strong [] [ text "Prompt: " ]
                    , text audioRecord.prompt
                    ]
                , div [ class "detail-row" ]
                    [ strong [] [ text "Model: " ]
                    , text audioRecord.modelId
                    ]
                , case audioRecord.collection of
                    Just coll ->
                        div [ class "detail-row" ]
                            [ strong [] [ text "Collection: " ]
                            , text coll
                            ]

                    Nothing ->
                        text ""
                , case audioRecord.duration of
                    Just dur ->
                        div [ class "detail-row" ]
                            [ strong [] [ text "Duration: " ]
                            , text (formatDuration dur)
                            ]

                    Nothing ->
                        text ""
                , div [ class "detail-row" ]
                    [ strong [] [ text "Created: " ]
                    , text audioRecord.createdAt
                    ]
                , div [ class "detail-row" ]
                    [ strong [] [ text "Status: " ]
                    , span
                        [ style "color" (if audioRecord.status == "failed" then "#c33" else "inherit")
                        , style "font-weight" (if audioRecord.status == "failed" then "bold" else "normal")
                        ]
                        [ text audioRecord.status ]
                    ]
                ]
            , div [ class "raw-data-section" ]
                [ button [ onClick ToggleRawData, class "toggle-raw-data" ]
                    [ text (if model.showRawData then "▼ Hide Raw Data" else "▶ Show Raw Data") ]
                , if model.showRawData then
                    div [ class "raw-data-content" ]
                        [ viewRawDataField "Parameters" audioRecord.parameters
                        , viewRawDataField "Metadata" audioRecord.metadata
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


truncateString : Int -> String -> String
truncateString maxLength str =
    if String.length str <= maxLength then
        str
    else
        String.left (maxLength - 3) str ++ "..."


-- HTTP


fetchAudio : Cmd Msg
fetchAudio =
    -- Cookies are sent automatically, no need for Authorization header
    Http.get
        { url = "/api/audio?limit=50"
        , expect = Http.expectJson AudioFetched (Decode.field "audio" (Decode.list audioDecoder))
        }


audioDecoder : Decode.Decoder AudioRecord
audioDecoder =
    Decode.map8
        (\id prompt audioUrl modelId createdAt collection parameters metadata ->
            { id = id
            , prompt = prompt
            , audioUrl = audioUrl
            , modelId = modelId
            , createdAt = createdAt
            , collection = collection
            , parameters = parameters
            , metadata = metadata
            , status = "completed"  -- Default, will be overridden below
            , duration = Nothing    -- Will be set below
            }
        )
        (Decode.field "id" Decode.int)
        (Decode.field "prompt" Decode.string)
        (Decode.field "audio_url" Decode.string)
        (Decode.field "model_id" Decode.string)
        (Decode.field "created_at" Decode.string)
        (Decode.maybe (Decode.field "collection" Decode.string))
        (Decode.maybe (Decode.field "parameters" Decode.value))
        (Decode.maybe (Decode.field "metadata" Decode.value))
        |> Decode.andThen
            (\record ->
                Decode.map2
                    (\status duration -> { record | status = status, duration = duration })
                    (Decode.oneOf
                        [ Decode.field "status" Decode.string
                        , Decode.succeed "completed"
                        ]
                    )
                    (Decode.maybe (Decode.field "duration" Decode.float))
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
