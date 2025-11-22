module AIVideoGallery exposing (Model, Msg(..), init, update, view, subscriptions)

import Html exposing (..)
import Html.Attributes exposing (..)
import Html.Events exposing (..)
import Http
import Json.Decode as Decode
import Time


-- MODEL


type alias Model =
    { videos : List AIVideoRecord
    , loading : Bool
    , error : Maybe String
    , selectedVideo : Maybe AIVideoRecord
    , currentPage : Int
    , totalVideos : Int
    , pageSize : Int
    }


type alias AIVideoRecord =
    { id : String
    , jobId : Int
    , subJobNumber : Int
    , modelId : String
    , videoUrl : String
    , thumbnailUrl : String
    , status : String
    , durationSeconds : Float
    , progress : Float
    , errorMessage : Maybe String
    , createdAt : String
    , completedAt : Maybe String
    , prompt : String
    }


init : ( Model, Cmd Msg )
init =
    ( { videos = []
      , loading = True
      , error = Nothing
      , selectedVideo = Nothing
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
    | VideosFetched (Result Http.Error (List AIVideoRecord, Int))
    | SelectVideo AIVideoRecord
    | CloseVideo
    | Tick Time.Posix
    | NextPage
    | PrevPage


update : Msg -> Model -> ( Model, Cmd Msg )
update msg model =
    case msg of
        NoOp ->
            ( model, Cmd.none )

        FetchVideos ->
            let
                offset =
                    (model.currentPage - 1) * model.pageSize
            in
            ( { model | loading = True }, fetchVideos model.pageSize offset )

        VideosFetched result ->
            case result of
                Ok ( videos, total ) ->
                    if videos == model.videos then
                        ( { model | loading = False, totalVideos = total }, Cmd.none )

                    else
                        ( { model | videos = videos, loading = False, error = Nothing, totalVideos = total }, Cmd.none )

                Err error ->
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
            ( { model | selectedVideo = Just video }, Cmd.none )

        CloseVideo ->
            ( { model | selectedVideo = Nothing }, Cmd.none )

        Tick _ ->
            let
                offset =
                    (model.currentPage - 1) * model.pageSize
            in
            ( model, fetchVideos model.pageSize offset )

        NextPage ->
            let
                maxPage =
                    ceiling (toFloat model.totalVideos / toFloat model.pageSize)

                newPage =
                    Basics.min (model.currentPage + 1) maxPage

                offset =
                    (newPage - 1) * model.pageSize
            in
            ( { model | currentPage = newPage, loading = True }, fetchVideos model.pageSize offset )

        PrevPage ->
            let
                newPage =
                    Basics.max (model.currentPage - 1) 1

                offset =
                    (newPage - 1) * model.pageSize
            in
            ( { model | currentPage = newPage, loading = True }, fetchVideos model.pageSize offset )


-- VIEW


view : Model -> Html Msg
view model =
    let
        maxPage =
            ceiling (toFloat model.totalVideos / toFloat model.pageSize)

        hasNextPage =
            model.currentPage < maxPage

        hasPrevPage =
            model.currentPage > 1
    in
    div [ class "video-gallery-page" ]
        [ h1 [] [ text "AI-Generated Videos" ]
        , button [ onClick FetchVideos, disabled model.loading, class "refresh-button" ]
            [ text
                (if model.loading then
                    "Loading..."

                 else
                    "Refresh"
                )
            ]
        , case model.error of
            Just err ->
                div [ class "error" ] [ text err ]

            Nothing ->
                text ""
        , if model.loading && List.isEmpty model.videos then
            div [ class "loading-text" ] [ text "Loading AI-generated videos..." ]

          else if List.isEmpty model.videos then
            div [ class "empty-state" ] [ text "No AI-generated videos yet. Create some using the image pairs endpoint!" ]

          else
            div []
                [ div [ class "videos-grid" ]
                    (List.map viewVideoCard model.videos)
                , viewPagination model.currentPage maxPage hasPrevPage hasNextPage
                ]
        , case model.selectedVideo of
            Just video ->
                viewVideoModal video

            Nothing ->
                text ""
        ]


viewVideoCard : AIVideoRecord -> Html Msg
viewVideoCard videoRecord =
    div [ class "video-card", onClick (SelectVideo videoRecord) ]
        [ div [ class "video-thumbnail" ]
            [ if String.isEmpty videoRecord.videoUrl then
                div
                    [ style "width" "100%"
                    , style "height" "100%"
                    , style "display" "flex"
                    , style "flex-direction" "column"
                    , style "align-items" "center"
                    , style "justify-content" "center"
                    , style "background"
                        (if videoRecord.status == "failed" then
                            "#c33"

                         else
                            "#333"
                        )
                    , style "color" "#fff"
                    , style "padding" "10px"
                    ]
                    [ div [ style "font-weight" "bold", style "margin-bottom" "5px" ]
                        [ text (String.toUpper videoRecord.status) ]
                    , case videoRecord.errorMessage of
                        Just err ->
                            div [ style "font-size" "12px", style "text-align" "center" ]
                                [ text (truncateString 60 err) ]

                        Nothing ->
                            text ""
                    ]

              else
                video
                    [ src videoRecord.videoUrl
                    , attribute "muted" "true"
                    , attribute "loop" "true"
                    , attribute "playsinline" "true"
                    , style "width" "100%"
                    , style "height" "100%"
                    , style "object-fit" "cover"
                    ]
                    []
            ]
        , div [ class "video-card-info" ]
            [ div [ class "video-prompt" ] [ text videoRecord.prompt ]
            , div [ class "video-meta" ]
                [ span [ class "video-model" ] [ text videoRecord.modelId ]
                , span [ class "video-date" ] [ text (formatDate videoRecord.createdAt) ]
                ]
            ]
        ]


viewVideoModal : AIVideoRecord -> Html Msg
viewVideoModal videoRecord =
    div [ class "modal-overlay", onClick CloseVideo ]
        [ div [ class "modal-content", onClickNoBubble ]
            [ button [ class "modal-close", onClick CloseVideo ] [ text "×" ]
            , h2 [] [ text "AI-Generated Video" ]
            , case videoRecord.errorMessage of
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
            , if not (String.isEmpty videoRecord.videoUrl) then
                video
                    [ src videoRecord.videoUrl
                    , controls True
                    , attribute "width" "100%"
                    , attribute "preload" "metadata"
                    , attribute "poster" videoRecord.thumbnailUrl
                    , class "modal-video"
                    ]
                    []

              else
                div
                    [ style "background" "#333"
                    , style "color" "#fff"
                    , style "padding" "40px"
                    , style "text-align" "center"
                    , style "border-radius" "4px"
                    , style "margin-bottom" "15px"
                    ]
                    [ text ("Video " ++ String.toUpper videoRecord.status) ]
            , div [ class "modal-details" ]
                [ div [ class "detail-row" ]
                    [ strong [] [ text "Job ID: " ]
                    , text (String.fromInt videoRecord.jobId ++ " (Clip #" ++ String.fromInt videoRecord.subJobNumber ++ ")")
                    ]
                , div [ class "detail-row" ]
                    [ strong [] [ text "Prompt: " ]
                    , text videoRecord.prompt
                    ]
                , div [ class "detail-row" ]
                    [ strong [] [ text "Model: " ]
                    , text videoRecord.modelId
                    ]
                , div [ class "detail-row" ]
                    [ strong [] [ text "Duration: " ]
                    , text (String.fromFloat videoRecord.durationSeconds ++ "s")
                    ]
                , div [ class "detail-row" ]
                    [ strong [] [ text "Created: " ]
                    , text videoRecord.createdAt
                    ]
                , case videoRecord.completedAt of
                    Just completed ->
                        div [ class "detail-row" ]
                            [ strong [] [ text "Completed: " ]
                            , text completed
                            ]

                    Nothing ->
                        text ""
                , div [ class "detail-row" ]
                    [ strong [] [ text "Status: " ]
                    , span
                        [ style "color"
                            (if videoRecord.status == "failed" then
                                "#c33"

                             else
                                "inherit"
                            )
                        , style "font-weight"
                            (if videoRecord.status == "failed" then
                                "bold"

                             else
                                "normal"
                            )
                        ]
                        [ text videoRecord.status ]
                    ]
                ]
            ]
        ]


onClickNoBubble : Html.Attribute Msg
onClickNoBubble =
    stopPropagationOn "click" (Decode.succeed ( NoOp, True ))


formatDate : String -> String
formatDate dateStr =
    String.left 19 dateStr


truncateString : Int -> String -> String
truncateString maxLength str =
    if String.length str <= maxLength then
        str

    else
        String.left (maxLength - 3) str ++ "..."


viewPagination : Int -> Int -> Bool -> Bool -> Html Msg
viewPagination currentPage maxPage hasPrevPage hasNextPage =
    div
        [ style "display" "flex"
        , style "justify-content" "center"
        , style "align-items" "center"
        , style "gap" "16px"
        , style "margin-top" "24px"
        ]
        [ button
            [ onClick PrevPage
            , disabled (not hasPrevPage)
            , style "padding" "10px 20px"
            ]
            [ text "← Previous" ]
        , div
            [ style "color" "#2c3e50"
            , style "font-weight" "600"
            ]
            [ text ("Page " ++ String.fromInt currentPage ++ " of " ++ String.fromInt maxPage) ]
        , button
            [ onClick NextPage
            , disabled (not hasNextPage)
            , style "padding" "10px 20px"
            ]
            [ text "Next →" ]
        ]


-- HTTP


fetchVideos : Int -> Int -> Cmd Msg
fetchVideos limit offset =
    Http.get
        { url = "/api/v3/ai-videos?limit=" ++ String.fromInt limit ++ "&offset=" ++ String.fromInt offset ++ "&status=completed"
        , expect = Http.expectJson VideosFetched videosResponseDecoder
        }


videosResponseDecoder : Decode.Decoder ( List AIVideoRecord, Int )
videosResponseDecoder =
    Decode.map2 Tuple.pair
        (Decode.at [ "data", "videos" ] (Decode.list videoDecoder))
        (Decode.at [ "data", "total" ] Decode.int)


videoDecoder : Decode.Decoder AIVideoRecord
videoDecoder =
    Decode.map8
        (\id jobId subJobNumber modelId videoUrl thumbnailUrl status durationSeconds ->
            { id = id
            , jobId = jobId
            , subJobNumber = subJobNumber
            , modelId = modelId
            , videoUrl = videoUrl
            , thumbnailUrl = thumbnailUrl
            , status = status
            , durationSeconds = durationSeconds
            , progress = 0.0
            , errorMessage = Nothing
            , createdAt = ""
            , completedAt = Nothing
            , prompt = ""
            }
        )
        (Decode.field "id" Decode.string)
        (Decode.field "jobId" Decode.int)
        (Decode.field "subJobNumber" Decode.int)
        (Decode.field "modelId" Decode.string)
        (Decode.field "videoUrl" Decode.string)
        (Decode.field "thumbnailUrl" Decode.string)
        (Decode.field "status" Decode.string)
        (Decode.field "durationSeconds" Decode.float)
        |> Decode.andThen
            (\record ->
                Decode.map5
                    (\progress errorMessage createdAt completedAt prompt ->
                        { record
                            | progress = progress
                            , errorMessage = errorMessage
                            , createdAt = createdAt
                            , completedAt = completedAt
                            , prompt = prompt
                        }
                    )
                    (Decode.field "progress" Decode.float)
                    (Decode.maybe (Decode.field "errorMessage" Decode.string))
                    (Decode.field "createdAt" Decode.string)
                    (Decode.maybe (Decode.field "completedAt" Decode.string))
                    (Decode.field "prompt" Decode.string)
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
    Time.every 5000 Tick
