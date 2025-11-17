module BriefGallery exposing (Model, Msg, init, initCmd, subscriptions, update, view)

import Browser.Navigation as Nav
import Html exposing (..)
import Html.Attributes exposing (..)
import Html.Events exposing (..)
import Http
import Json.Decode as Decode
import Json.Decode.Pipeline as Pipeline
import Json.Encode as Encode
import Route exposing (Route)


-- MODEL


type alias Model =
    { briefs : List CreativeBrief
    , currentPage : Int
    , totalPages : Int
    , isLoading : Bool
    , error : Maybe String
    , selectedBrief : Maybe CreativeBrief
    , navigationKey : Nav.Key
    }


type alias CreativeBrief =
    { id : String
    , userId : Int
    , promptText : Maybe String
    , imageUrl : Maybe String
    , videoUrl : Maybe String
    , creativeDirection : Decode.Value
    , scenes : List Scene
    , confidenceScore : Maybe Float
    , createdAt : String
    , updatedAt : String
    }


type alias Scene =
    { id : String
    , sceneNumber : Int
    , purpose : String
    , duration : Float
    , visual : Maybe VisualDetails
    }


type alias VisualDetails =
    { shotType : Maybe String
    , subject : Maybe String
    , generationPrompt : Maybe String
    }


init : Nav.Key -> ( Model, Cmd Msg )
init key =
    ( { briefs = []
      , currentPage = 1
      , totalPages = 1
      , isLoading = True
      , error = Nothing
      , selectedBrief = Nothing
      , navigationKey = key
      }
    , loadBriefs 1
    )


initCmd : Model -> Cmd Msg
initCmd model =
    loadBriefs 1


-- UPDATE


type Msg
    = LoadBriefs Int
    | BriefsLoaded (Result Http.Error BriefsResponse)
    | SelectBrief String
    | RefineBrief String
    | DeleteBrief String
    | NextPage
    | PrevPage
    | NavigateTo Route
    | CloseBriefDetail
    | GenerateFromBrief String
    | GenerateImageFromBrief String
    | GenerateVideoFromBrief String
    | GenerationResponse (Result Http.Error String)


update : Msg -> Model -> ( Model, Cmd Msg )
update msg model =
    case msg of
        LoadBriefs page ->
            ( { model | isLoading = True, error = Nothing, currentPage = page }
            , loadBriefs page
            )

        BriefsLoaded result ->
            case result of
                Ok response ->
                    ( { model
                        | briefs = response.briefs
                        , isLoading = False
                        , error = Nothing
                        , totalPages = response.totalPages
                      }
                    , Cmd.none
                    )

                Err error ->
                    ( { model
                        | isLoading = False
                        , error = Just (httpErrorToString error)
                      }
                    , Cmd.none
                    )

        SelectBrief briefId ->
            ( model, Nav.pushUrl model.navigationKey ("/creative?brief=" ++ briefId) )

        RefineBrief briefId ->
            ( model, Nav.pushUrl model.navigationKey ("/creative?refine=" ++ briefId) )

        DeleteBrief briefId ->
            ( model, deleteBrief briefId model.navigationKey )

        NextPage ->
            ( { model | currentPage = model.currentPage + 1 }, loadBriefs (model.currentPage + 1) )

        PrevPage ->
            if model.currentPage > 1 then
                ( { model | currentPage = model.currentPage - 1 }, loadBriefs (model.currentPage - 1) )

            else
                ( model, Cmd.none )

        NavigateTo route ->
            ( model, Nav.pushUrl model.navigationKey (Route.toHref route) )

        CloseBriefDetail ->
            ( { model | selectedBrief = Nothing }, Cmd.none )

        GenerateFromBrief briefId ->
            ( model, generateSceneFromBrief briefId )

        GenerateImageFromBrief briefId ->
            ( model, generateImageFromBrief briefId )

        GenerateVideoFromBrief briefId ->
            ( model, generateVideoFromBrief briefId )

        GenerationResponse result ->
            case result of
                Ok _ ->
                    ( model, Cmd.none )

                Err _ ->
                    ( { model | error = Just "Generation failed" }, Cmd.none )


-- HTTP


type alias BriefsResponse =
    { briefs : List CreativeBrief
    , totalPages : Int
    }


loadBriefs : Int -> Cmd Msg
loadBriefs page =
    Http.get
        { url = "/api/creative/briefs?page=" ++ String.fromInt page ++ "&limit=12"
        , expect = Http.expectJson BriefsLoaded decodeBriefsResponse
        }


decodeVisualDetails : Decode.Decoder VisualDetails
decodeVisualDetails =
    Decode.map3 VisualDetails
        (Decode.maybe (Decode.field "shot_type" Decode.string))
        (Decode.maybe (Decode.field "subject" Decode.string))
        (Decode.maybe (Decode.field "generation_prompt" Decode.string))


decodeBriefsResponse : Decode.Decoder BriefsResponse
decodeBriefsResponse =
    Decode.map2 BriefsResponse
        (Decode.field "briefs" (Decode.list decodeCreativeBrief))
        (Decode.field "totalPages" Decode.int)


decodeCreativeBrief : Decode.Decoder CreativeBrief
decodeCreativeBrief =
    Decode.succeed CreativeBrief
        |> Pipeline.required "id" Decode.string
        |> Pipeline.required "user_id" Decode.int
        |> Pipeline.optional "prompt_text" (Decode.nullable Decode.string) Nothing
        |> Pipeline.optional "image_url" (Decode.nullable Decode.string) Nothing
        |> Pipeline.optional "video_url" (Decode.nullable Decode.string) Nothing
        |> Pipeline.required "creative_direction" Decode.value
        |> Pipeline.required "scenes" (Decode.list decodeScene)
        |> Pipeline.optional "confidence_score" (Decode.nullable Decode.float) Nothing
        |> Pipeline.required "created_at" Decode.string
        |> Pipeline.required "updated_at" Decode.string


decodeScene : Decode.Decoder Scene
decodeScene =
    Decode.map5 Scene
        (Decode.field "id" Decode.string)
        (Decode.field "scene_number" Decode.int)
        (Decode.field "purpose" Decode.string)
        (Decode.field "duration" Decode.float)
        (Decode.maybe (Decode.field "visual" decodeVisualDetails))


generateSceneFromBrief : String -> Cmd Msg
generateSceneFromBrief briefId =
    Http.post
        { url = "/api/generate"
        , body = Http.jsonBody (Encode.object [ ( "prompt", Encode.string "Generate scene from brief" ), ( "brief_id", Encode.string briefId ) ])
        , expect = Http.expectWhatever (\_ -> LoadBriefs 1)  -- Reload briefs after generation
        }


generateImageFromBrief : String -> Cmd Msg
generateImageFromBrief briefId =
    Http.post
        { url = "/api/run-image-model"
        , body = Http.jsonBody (Encode.object [
            ( "model_id", Encode.string "stability-ai/sdxl" ),
            ( "input", Encode.object [ ( "prompt", Encode.string "Generate image from creative brief" ) ] ),
            ( "brief_id", Encode.string briefId )
        ])
        , expect = Http.expectJson GenerationResponse decodeImageGenerationResponse
        }


generateVideoFromBrief : String -> Cmd Msg
generateVideoFromBrief briefId =
    Http.post
        { url = "/api/run-video-model"
        , body = Http.jsonBody (Encode.object [
            ( "model_id", Encode.string "stability-ai/stable-video-diffusion" ),
            ( "input", Encode.object [ ( "prompt", Encode.string "Generate video from creative brief" ) ] ),
            ( "brief_id", Encode.string briefId )
        ])
        , expect = Http.expectJson GenerationResponse decodeVideoGenerationResponse
        }


decodeImageGenerationResponse : Decode.Decoder String
decodeImageGenerationResponse =
    Decode.map (\id -> "Image generation started with ID: " ++ String.fromInt id) (Decode.field "image_id" Decode.int)


decodeVideoGenerationResponse : Decode.Decoder String
decodeVideoGenerationResponse =
    Decode.map (\id -> "Video generation started with ID: " ++ String.fromInt id) (Decode.field "video_id" Decode.int)


deleteBrief : String -> Nav.Key -> Cmd Msg
deleteBrief briefId key =
    Http.request
        { method = "DELETE"
        , headers = []
        , url = "/api/creative/briefs/" ++ briefId
        , body = Http.emptyBody
        , expect = Http.expectWhatever (\_ -> LoadBriefs 1)
        , timeout = Nothing
        , tracker = Nothing
        }


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
            "Bad status: " ++ String.fromInt status

        Http.BadBody message ->
            "Bad response: " ++ message


-- VIEW


view : Model -> Html Msg
view model =
    div [ style "padding" "20px", style "max-width" "800px", style "margin" "0 auto" ]
        [ h2 [] [ text "Brief Gallery" ]
        , if model.isLoading then
            div [ style "text-align" "center", style "color" "#666" ] [ text "Loading briefs..." ]

          else
            div []
                [ button [ onClick (NavigateTo Route.CreativeBriefEditor), style "background-color" "#4CAF50", style "color" "white", style "padding" "10px 16px", style "border" "none", style "border-radius" "4px", style "margin-bottom" "10px" ] [ text "New Brief" ]
                , ul [ style "list-style" "none", style "padding" "0" ] (List.map viewBriefCard model.briefs)
                , div [ style "margin-top" "20px", style "display" "flex", style "justify-content" "space-between" ]
                    [ button [ onClick PrevPage, style "padding" "10px 16px", style "border" "1px solid #ccc", style "border-radius" "4px" ] [ text "Previous" ]
                    , p [] [ text ("Page " ++ String.fromInt model.currentPage) ]
                    , button [ onClick NextPage, style "padding" "10px 16px", style "border" "1px solid #ccc", style "border-radius" "4px" ] [ text "Next" ]
                    ]
                ]
        , case model.error of
            Just err ->
                div [ style "color" "red", style "margin-top" "10px", style "padding" "10px", style "background" "#ffebee", style "border-radius" "4px" ] [ text ("Error: " ++ err) ]

            Nothing ->
                text ""
        ]


viewControls : Model -> Html Msg
viewControls model =
    div [ class "gallery-controls" ]
        [ a [ href (Route.toHref Route.CreativeBriefEditor), class "create-btn" ]
            [ text "Create New Brief" ]
        , div [ class "pagination" ]
            [ button
                [ onClick (LoadBriefs (model.currentPage - 1))
                , disabled (model.currentPage <= 1 || model.isLoading)
                ]
                [ text "Previous" ]
            , span [] [ text ("Page " ++ String.fromInt model.currentPage) ]
            , button
                [ onClick (LoadBriefs (model.currentPage + 1))
                , disabled model.isLoading
                ]
                [ text "Next" ]
            ]
        ]


viewBriefsGrid : Model -> Html Msg
viewBriefsGrid model =
    if model.isLoading then
        div [ class "loading" ] [ text "Loading briefs..." ]
    else if List.isEmpty model.briefs then
        div [ class "empty-state" ]
            [ text "No creative briefs found. "
            , a [ href (Route.toHref Route.CreativeBriefEditor) ] [ text "Create your first one!" ]
            ]
    else
        div [ class "briefs-grid" ]
            (List.map viewBriefCard model.briefs)


viewBriefCard : CreativeBrief -> Html Msg
viewBriefCard brief =
    div [ class "brief-card", onClick (SelectBrief brief.id) ]
        [ div [ class "brief-header" ]
            [ h3 [] [ text (brief.promptText |> Maybe.withDefault "Untitled Brief") ]
            , div [ class "brief-meta" ]
                [ text ("Scenes: " ++ String.fromInt (List.length brief.scenes))
                , case brief.confidenceScore of
                    Just score ->
                        text (" | Confidence: " ++ String.fromFloat score)

                    Nothing ->
                        text ""
                ]
            ]
        , div [ class "brief-preview" ]
            [ case List.head brief.scenes of
                Just firstScene ->
                    div [ class "scene-preview" ]
                        [ text ("First scene: " ++ firstScene.purpose ++ " (" ++ String.fromFloat firstScene.duration ++ "s)") ]

                Nothing ->
                    text "No scenes"
            ]
        , div [ class "brief-actions" ]
            [ button [ onClick (GenerateFromBrief brief.id), class "generate-btn" ]
                [ text "Generate Scene" ]
            , button [ onClick (GenerateImageFromBrief brief.id), class "generate-btn" ]
                [ text "Generate Image" ]
            , button [ onClick (GenerateVideoFromBrief brief.id), class "generate-btn" ]
                [ text "Generate Video" ]
            ]
        ]


viewBriefDetail : Model -> Html Msg
viewBriefDetail model =
    case model.selectedBrief of
        Just brief ->
            div [ class "brief-detail-overlay", onClick CloseBriefDetail ]
                [ div [ class "brief-detail" ]  -- Removed onClick to prevent overlay close
                    [ button [ class "close-btn", onClick CloseBriefDetail ] [ text "×" ]
                    , h2 [] [ text (brief.promptText |> Maybe.withDefault "Creative Brief") ]
                    , div [ class "brief-info" ]
                        [ p [] [ text ("Created: " ++ brief.createdAt) ]
                        , p [] [ text ("Scenes: " ++ String.fromInt (List.length brief.scenes)) ]
                        , case brief.confidenceScore of
                            Just score ->
                                p [] [ text ("Confidence: " ++ String.fromFloat score) ]

                            Nothing ->
                                text ""
                        ]
                    , div [ class "scenes-detail" ]
                        (List.map viewSceneDetail brief.scenes)
                    , div [ class "detail-actions" ]
                        [ button [ onClick (GenerateFromBrief brief.id), class "generate-btn" ]
                            [ text "Generate Physics Scene" ]
                        ]
                    ]
                ]

        Nothing ->
            text ""


viewSceneDetail : Scene -> Html Msg
viewSceneDetail scene =
    div [ class "scene-detail" ]
        [ h4 [] [ text ("Scene " ++ String.fromInt scene.sceneNumber ++ ": " ++ scene.purpose) ]
        , div [ class "scene-info" ]
            [ text ("Duration: " ++ String.fromFloat scene.duration ++ " seconds") ]
        , case scene.visual of
            Just visual ->
                case visual.generationPrompt of
                    Just prompt ->
                        div [ class "generation-prompt" ]
                            [ strong [] [ text "Generation Prompt: " ]
                            , text prompt
                            ]

                    Nothing ->
                        text ""

            Nothing ->
                text ""
        ]


subscriptions : Model -> Sub Msg
subscriptions model =
    Sub.none
