module VideoToTextGallery exposing (Model, Msg(..), init, update, view, subscriptions, fetchVideos)

import Html exposing (..)
import Html.Attributes exposing (..)
import Html.Events exposing (..)
import Http
import Json.Decode as Decode
import Json.Encode as Encode
import Time


-- MODEL


type alias Model =
    { videos : List VideoToTextRecord
    , loading : Bool
    , error : Maybe String
    , selectedVideo : Maybe VideoToTextRecord
    , showRawData : Bool
    , currentPage : Int
    , totalVideos : Int
    , pageSize : Int
    }


type alias VideoToTextRecord =
    { id : Int
    , prompt : String
    , outputText : String
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
      , currentPage = 1
      , totalVideos = 0
      , pageSize = 20
      }
    , fetchVideos 20 0
    )


-- UPDATE


type Msg
    = NoOp
    | FetchVideos
    | VideosFetched (Result Http.Error (List VideoToTextRecord, Int))
    | SelectVideo VideoToTextRecord
    | CloseVideo
    | ToggleRawData
    | Tick Time.Posix
    | NextPage
    | PrevPage
    | GoToPage Int


update : Msg -> Model -> ( Model, Cmd Msg )
update msg model =
    case msg of
        NoOp ->
            ( model, Cmd.none )

        FetchVideos ->
            let
                offset = (model.currentPage - 1) * model.pageSize
            in
            ( { model | loading = True }, fetchVideos model.pageSize offset )

        VideosFetched result ->
            case result of
                Ok (videos, total) ->
                    -- Only update if videos actually changed
                    if videos == model.videos then
                        ( { model | loading = False, totalVideos = total }, Cmd.none )
                    else
                        ( { model | videos = videos, loading = False, error = Nothing, totalVideos = total }, Cmd.none )

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

        SelectVideo video ->
            ( { model | selectedVideo = Just video, showRawData = False }, Cmd.none )

        CloseVideo ->
            ( { model | selectedVideo = Nothing, showRawData = False }, Cmd.none )

        ToggleRawData ->
            ( { model | showRawData = not model.showRawData }, Cmd.none )

        Tick _ ->
            -- Don't set loading=True on background refresh to prevent flicker
            let
                offset = (model.currentPage - 1) * model.pageSize
            in
            ( model, fetchVideos model.pageSize offset )

        NextPage ->
            let
                maxPage = ceiling (toFloat model.totalVideos / toFloat model.pageSize)
                newPage = Basics.min (model.currentPage + 1) maxPage
                offset = (newPage - 1) * model.pageSize
            in
            ( { model | currentPage = newPage, loading = True }, fetchVideos model.pageSize offset )

        PrevPage ->
            let
                newPage = Basics.max (model.currentPage - 1) 1
                offset = (newPage - 1) * model.pageSize
            in
            ( { model | currentPage = newPage, loading = True }, fetchVideos model.pageSize offset )

        GoToPage page ->
            let
                maxPage = ceiling (toFloat model.totalVideos / toFloat model.pageSize)
                newPage = clamp 1 maxPage page
                offset = (newPage - 1) * model.pageSize
            in
            ( { model | currentPage = newPage, loading = True }, fetchVideos model.pageSize offset )


-- VIEW


view : Model -> Html Msg
view model =
    let
        maxPage = ceiling (toFloat model.totalVideos / toFloat model.pageSize)
        hasNextPage = model.currentPage < maxPage
        hasPrevPage = model.currentPage > 1
    in
    div [ class "video-gallery-page" ]
        [ h1 [] [ text "Generated Video-to-Text Results" ]
        , button [ onClick FetchVideos, disabled model.loading, class "refresh-button" ]
            [ text (if model.loading then "Loading..." else "Refresh") ]
        , case model.error of
            Just err ->
                div [ class "error" ] [ text err ]

            Nothing ->
                text ""
        , if model.loading && List.isEmpty model.videos then
            div [ class "loading-text" ] [ text "Loading results..." ]

          else if List.isEmpty model.videos then
            div [ class "empty-state" ] [ text "No video-to-text results yet. Go to the Video to Text page to generate some!" ]

          else
            div []
                [ div [ class "videos-grid" ]
                    (List.map viewVideoCard model.videos)
                , viewPagination model.currentPage maxPage hasPrevPage hasNextPage
                ]
        , case model.selectedVideo of
            Just video ->
                viewVideoModal model video

            Nothing ->
                text ""
        ]


viewVideoCard : VideoToTextRecord -> Html Msg
viewVideoCard record =
    let
        errorMessage =
            extractErrorMessage record

        textPreview =
            if String.isEmpty record.outputText then
                "(No text generated)"
            else
                truncateString 100 record.outputText
    in
    div [ class "video-card", onClick (SelectVideo record) ]
        [ div [ class "video-thumbnail" ]
            [ if String.isEmpty record.outputText then
                div
                    [ style "width" "100%"
                    , style "height" "100%"
                    , style "display" "flex"
                    , style "flex-direction" "column"
                    , style "align-items" "center"
                    , style "justify-content" "center"
                    , style "background" (if record.status == "failed" then "#c33" else "#333")
                    , style "color" "#fff"
                    , style "padding" "10px"
                    ]
                    [ div [ style "font-weight" "bold", style "margin-bottom" "5px" ]
                        [ text (String.toUpper record.status) ]
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
                    , style "padding" "15px"
                    , style "background" "#f5f5f5"
                    , style "overflow" "hidden"
                    , style "display" "flex"
                    , style "align-items" "center"
                    , style "justify-content" "center"
                    ]
                    [ div [ style "font-size" "14px", style "color" "#333", style "text-align" "center" ]
                        [ text textPreview ]
                    ]
            ]
        , div [ class "video-card-info" ]
            [ div [ class "video-prompt" ] [ text record.prompt ]
            , div [ class "video-meta" ]
                [ span [ class "video-model" ] [ text record.modelId ]
                , span [ class "video-date" ] [ text (formatDate record.createdAt) ]
                ]
            ]
        ]


viewVideoModal : Model -> VideoToTextRecord -> Html Msg
viewVideoModal model record =
    let
        errorMessage =
            extractErrorMessage record
    in
    div [ class "modal-overlay", onClick CloseVideo ]
        [ div [ class "modal-content", onClickNoBubble ]
            [ button [ class "modal-close", onClick CloseVideo ] [ text "×" ]
            , h2 [] [ text "Generated Text Result" ]
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
            , if not (String.isEmpty record.outputText) then
                div [ class "text-output-container" ]
                    [ h3 [] [ text "Generated Text" ]
                    , pre
                        [ class "output-text-content"
                        , style "background" "#f5f5f5"
                        , style "padding" "20px"
                        , style "border-radius" "4px"
                        , style "border" "1px solid #ddd"
                        , style "white-space" "pre-wrap"
                        , style "word-wrap" "break-word"
                        , style "max-height" "400px"
                        , style "overflow-y" "auto"
                        , style "font-family" "monospace"
                        , style "font-size" "14px"
                        , style "line-height" "1.5"
                        ]
                        [ text record.outputText ]
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
                    [ text ("Generation " ++ String.toUpper record.status) ]
            , div [ class "modal-details" ]
                [ div [ class "detail-row" ]
                    [ strong [] [ text "Prompt: " ]
                    , text record.prompt
                    ]
                , div [ class "detail-row" ]
                    [ strong [] [ text "Model: " ]
                    , text record.modelId
                    ]
                , case record.collection of
                    Just coll ->
                        div [ class "detail-row" ]
                            [ strong [] [ text "Collection: " ]
                            , text coll
                            ]

                    Nothing ->
                        text ""
                , div [ class "detail-row" ]
                    [ strong [] [ text "Created: " ]
                    , text record.createdAt
                    ]
                , div [ class "detail-row" ]
                    [ strong [] [ text "Status: " ]
                    , span
                        [ style "color" (if record.status == "failed" then "#c33" else "inherit")
                        , style "font-weight" (if record.status == "failed" then "bold" else "normal")
                        ]
                        [ text record.status ]
                    ]
                ]
            , div [ class "raw-data-section" ]
                [ button [ onClick ToggleRawData, class "toggle-raw-data" ]
                    [ text (if model.showRawData then "▼ Hide Raw Data" else "▶ Show Raw Data") ]
                , if model.showRawData then
                    div [ class "raw-data-content" ]
                        [ viewRawDataField "Parameters" record.parameters
                        , viewRawDataField "Metadata" record.metadata
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


extractErrorMessage : VideoToTextRecord -> Maybe String
extractErrorMessage record =
    -- Try to extract error message from metadata
    case record.metadata of
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


viewPagination : Int -> Int -> Bool -> Bool -> Html Msg
viewPagination currentPage maxPage hasPrevPage hasNextPage =
    div [ class "pagination" ]
        [ button
            [ onClick PrevPage
            , disabled (not hasPrevPage)
            , class "pagination-button"
            ]
            [ text "← Previous" ]
        , div [ class "pagination-info" ]
            [ text ("Page " ++ String.fromInt currentPage ++ " of " ++ String.fromInt maxPage) ]
        , button
            [ onClick NextPage
            , disabled (not hasNextPage)
            , class "pagination-button"
            ]
            [ text "Next →" ]
        ]


-- HTTP


fetchVideos : Int -> Int -> Cmd Msg
fetchVideos limit offset =
    -- Cookies are sent automatically, no need for Authorization header
    Http.get
        { url = "/api/videos?collection=video-to-text&limit=" ++ String.fromInt limit ++ "&offset=" ++ String.fromInt offset
        , expect = Http.expectJson VideosFetched videosResponseDecoder
        }


videosResponseDecoder : Decode.Decoder (List VideoToTextRecord, Int)
videosResponseDecoder =
    Decode.map2 Tuple.pair
        (Decode.field "videos" (Decode.list videoDecoder))
        (Decode.field "total" Decode.int)


videoDecoder : Decode.Decoder VideoToTextRecord
videoDecoder =
    Decode.map8
        (\id prompt outputText modelId createdAt collection parameters metadata ->
            { id = id
            , prompt = prompt
            , outputText = outputText
            , modelId = modelId
            , createdAt = createdAt
            , collection = collection
            , parameters = parameters
            , metadata = metadata
            , status = "completed"  -- Default, will be overridden below
            }
        )
        (Decode.field "id" Decode.int)
        (Decode.field "prompt" Decode.string)
        (Decode.oneOf
            [ Decode.field "output_text" Decode.string
            , Decode.field "video_url" Decode.string  -- Fallback for compatibility
            , Decode.succeed ""
            ]
        )
        (Decode.field "model_id" Decode.string)
        (Decode.field "created_at" Decode.string)
        (Decode.maybe (Decode.field "collection" Decode.string))
        (Decode.maybe (Decode.field "parameters" Decode.value))
        (Decode.maybe (Decode.field "metadata" Decode.value))
        |> Decode.andThen
            (\record ->
                Decode.map
                    (\status -> { record | status = status })
                    (Decode.oneOf
                        [ Decode.field "status" Decode.string
                        , Decode.succeed "completed"
                        ]
                    )
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
