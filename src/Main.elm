port module Main exposing (main)

import Browser
import Browser.Events
import Browser.Navigation as Nav
import Dict exposing (Dict)
import Html exposing (..)
import Html.Attributes exposing (..)
import Html.Events exposing (..)
import Http
import Json.Decode as Decode
import Json.Encode as Encode
import Route exposing (Route)
import Task
import Process
import Url exposing (Url)
import Video
import VideoDetail
import VideoGallery
import SimulationGallery
import Image
import ImageDetail
import ImageGallery
import Audio
import AudioDetail
import AudioGallery
import Auth
import CreativeBriefEditor
import BriefGallery
import Browser.Navigation as Nav


-- MAIN


main : Program () Model Msg
main =
    Browser.application
        { init = init
        , update = update
        , view = view
        , subscriptions = subscriptions
        , onUrlChange = UrlChanged
        , onUrlRequest = LinkClicked
        }


-- MODEL


type alias Model =
    { key : Nav.Key
    , url : Url
    , route : Maybe Route
    , scene : Scene
    , uiState : UiState
    , simulationState : SimulationState
    , initialScene : Maybe Scene
    , history : List Scene
    , future : List Scene
    , ctrlPressed : Bool
    , videoModel : Video.Model
    , videoDetailModel : Maybe VideoDetail.Model
    , galleryModel : VideoGallery.Model
    , simulationGalleryModel : SimulationGallery.Model
    , imageModel : Image.Model
    , imageDetailModel : Maybe ImageDetail.Model
    , imageGalleryModel : ImageGallery.Model
    , audioModel : Audio.Model
    , audioDetailModel : Maybe AudioDetail.Model
    , audioGalleryModel : AudioGallery.Model
    , authModel : Auth.Auth
    , pendingVideoFromImage : Maybe { modelId : String, imageUrl : String }
    , creativeBriefEditorModel : CreativeBriefEditor.Model
    , briefGalleryModel : BriefGallery.Model
    }


type alias Scene =
    { objects : Dict String PhysicsObject
    , selectedObject : Maybe String
    }


type alias UiState =
    { textInput : String
    , isGenerating : Bool
    , errorMessage : Maybe String
    , refineInput : String
    , isRefining : Bool
    }


type alias SimulationState =
    { isRunning : Bool
    , transformMode : TransformMode
    }


type TransformMode
    = Translate
    | Rotate
    | Scale


type alias PhysicsObject =
    { id : String
    , transform : Transform
    , physicsProperties : PhysicsProperties
    , visualProperties : VisualProperties
    , description : Maybe String
    }


type alias Transform =
    { position : Vec3
    , rotation : Vec3
    , scale : Vec3
    }


type alias Vec3 =
    { x : Float
    , y : Float
    , z : Float
    }


type alias PhysicsProperties =
    { mass : Float
    , friction : Float
    , restitution : Float
    }


type alias VisualProperties =
    { color : String
    , shape : Shape
    }


type Shape
    = Box
    | Sphere
    | Cylinder


init : () -> Url -> Nav.Key -> ( Model, Cmd Msg )
init _ url key =
    let
        ( videoModel, videoCmd ) =
            Video.init

        ( galleryModel, galleryCmd ) =
            VideoGallery.init

        ( simulationGalleryModel, simulationGalleryCmd ) =
            SimulationGallery.init

        ( imageModel, imageCmd ) =
            Image.init

        ( imageGalleryModel, imageGalleryCmd ) =
            ImageGallery.init

        ( audioModel, audioCmd ) =
            Audio.init

        ( audioGalleryModel, audioGalleryCmd ) =
            AudioGallery.init

        ( creativeBriefEditorModel, creativeBriefEditorCmd ) =
            CreativeBriefEditor.init key

        ( briefGalleryModel, briefGalleryCmd ) =
            BriefGallery.init key

        route =
            Route.fromUrl url
    in
    ( { key = key
      , url = url
      , route = route
      , scene = { objects = Dict.empty, selectedObject = Nothing }
      , uiState = { textInput = "", isGenerating = False, errorMessage = Nothing, refineInput = "", isRefining = False }
      , simulationState = { isRunning = False, transformMode = Translate }
      , initialScene = Nothing
      , history = []
      , future = []
      , ctrlPressed = False
      , videoModel = videoModel
      , videoDetailModel = Nothing
      , galleryModel = galleryModel
      , simulationGalleryModel = simulationGalleryModel
      , imageModel = imageModel
      , imageDetailModel = Nothing
      , imageGalleryModel = imageGalleryModel
      , audioModel = audioModel
      , audioDetailModel = Nothing
      , audioGalleryModel = audioGalleryModel
      , authModel = Auth.init
      , pendingVideoFromImage = Nothing
      , creativeBriefEditorModel = creativeBriefEditorModel
      , briefGalleryModel = briefGalleryModel
      }
    , Cmd.batch
        [ Cmd.map VideoMsg videoCmd
        , Cmd.map GalleryMsg galleryCmd
        , Cmd.map SimulationGalleryMsg simulationGalleryCmd
        , Cmd.map ImageMsg imageCmd
        , Cmd.map ImageGalleryMsg imageGalleryCmd
        , Cmd.map AudioMsg audioCmd
        , Cmd.map AudioGalleryMsg audioGalleryCmd
        , Cmd.map CreativeBriefEditorMsg creativeBriefEditorCmd
        , Cmd.map BriefGalleryMsg briefGalleryCmd
        , Cmd.map AuthMsg Auth.checkAuth
        ]
    )


-- UPDATE


type Msg
    = NoOp
    | LinkClicked Browser.UrlRequest
    | UrlChanged Url
    | UpdateTextInput String
    | GenerateScene
    | SceneGenerated Encode.Value
    | SceneGeneratedResult (Result Http.Error Scene)
    | ObjectClicked String
    | UpdateObjectTransform String Transform
    | UpdateObjectProperty String String Float
    | UpdateObjectDescription String String
    | ToggleSimulation
    | ResetSimulation
    | SetTransformMode TransformMode
    | UpdateRefineInput String
    | RefineScene
    | SceneRefined (Result Http.Error Scene)
    | Undo
    | Redo
    | SaveScene
    | LoadScene
    | SceneLoadedFromStorage Encode.Value
    | KeyDown String
    | KeyUp String
    | ClearError
    | SelectionChanged (Maybe String)
    | TransformUpdated { objectId : String, transform : Transform }
    | VideoMsg Video.Msg
    | VideoDetailMsg VideoDetail.Msg
    | GalleryMsg VideoGallery.Msg
    | SimulationGalleryMsg SimulationGallery.Msg
    | ImageMsg Image.Msg
    | ImageDetailMsg ImageDetail.Msg
    | ImageGalleryMsg ImageGallery.Msg
    | AudioMsg Audio.Msg
    | AudioDetailMsg AudioDetail.Msg
    | AudioGalleryMsg AudioGallery.Msg
    | AuthMsg Auth.Msg
    | CreativeBriefEditorMsg CreativeBriefEditor.Msg
    | BriefGalleryMsg BriefGallery.Msg
    | NavigateTo Route


update : Msg -> Model -> ( Model, Cmd Msg )
update msg model =
    case msg of
        NoOp ->
            ( model, Cmd.none )

        LinkClicked urlRequest ->
            case urlRequest of
                Browser.Internal url ->
                    ( model, Nav.pushUrl model.key (Url.toString url) )

                Browser.External href ->
                    ( model, Nav.load href )

        UrlChanged url ->
            let
                newRoute = Route.fromUrl url

                videoDetailModel =
                    case newRoute of
                        Just (Route.VideoDetail videoId) ->
                            let
                                ( detailModel, detailCmd ) = VideoDetail.init videoId
                            in
                            Just detailModel

                        _ ->
                            Nothing

                imageDetailModel =
                    case newRoute of
                        Just (Route.ImageDetail imageId) ->
                            let
                                ( detailModel, detailCmd ) = ImageDetail.init imageId
                            in
                            Just detailModel

                        _ ->
                            Nothing

                audioDetailModel =
                    case newRoute of
                        Just (Route.AudioDetail audioId) ->
                            let
                                ( detailModel, detailCmd ) = AudioDetail.init audioId
                            in
                            Just detailModel

                        _ ->
                            Nothing

                creativeBriefEditorModel =
                    case newRoute of
                        Just Route.CreativeBriefEditor ->
                            let
                                ( editorModel, editorCmd ) = CreativeBriefEditor.init model.key
                            in
                            editorModel

                        _ ->
                            model.creativeBriefEditorModel

                ( briefGalleryModel, briefGalleryInitCmd ) =
                    case newRoute of
                        Just Route.BriefGallery ->
                            BriefGallery.init model.key

                        _ ->
                            ( model.briefGalleryModel, Cmd.none )

                galleryCmd =
                    case newRoute of
                        Just Route.Gallery ->
                            Task.perform (always (GalleryMsg VideoGallery.FetchVideos)) (Task.succeed ())

                        _ ->
                            Cmd.none

                imageGalleryCmd =
                    case newRoute of
                        Just Route.ImageGallery ->
                            Task.perform (always (ImageGalleryMsg ImageGallery.FetchImages)) (Task.succeed ())

                        _ ->
                            Cmd.none

                audioGalleryCmd =
                    case newRoute of
                        Just Route.AudioGallery ->
                            Task.perform (always (AudioGalleryMsg AudioGallery.FetchAudio)) (Task.succeed ())

                        _ ->
                            Cmd.none

                videoPrefillCmd =
                    case ( newRoute, model.pendingVideoFromImage ) of
                        ( Just Route.Videos, Just { modelId, imageUrl } ) ->
                            Cmd.batch
                                [ Task.perform (always (VideoMsg (Video.SelectCollection "image-to-video"))) (Task.succeed ())
                                , Process.sleep 50 |> Task.andThen (\_ -> Task.succeed (VideoMsg (Video.SelectModel modelId))) |> Task.perform identity
                                , Process.sleep 100 |> Task.andThen (\_ -> Task.succeed (VideoMsg (Video.UpdateParameter "image" imageUrl))) |> Task.perform identity
                                ]

                        _ ->
                            Cmd.none

                clearedPending =
                    case ( newRoute, model.pendingVideoFromImage ) of
                        ( Just Route.Videos, Just _ ) ->
                            Nothing

                        _ ->
                            model.pendingVideoFromImage

                videoDetailCmd =
                    Cmd.none

                imageDetailCmd =
                    Cmd.none

                audioDetailCmd =
                    Cmd.none

                creativeBriefEditorCmd =
                    Cmd.none

                briefGalleryCmd =
                    case newRoute of
                        Just Route.BriefGallery ->
                            Cmd.map BriefGalleryMsg (BriefGallery.initCmd briefGalleryModel)

                        _ ->
                            Cmd.none
            in
            ( { model | url = url, route = newRoute, videoDetailModel = videoDetailModel, imageDetailModel = imageDetailModel, audioDetailModel = audioDetailModel, creativeBriefEditorModel = creativeBriefEditorModel, briefGalleryModel = briefGalleryModel, pendingVideoFromImage = clearedPending }
            , Cmd.batch [ videoDetailCmd, imageDetailCmd, audioDetailCmd, creativeBriefEditorCmd, briefGalleryCmd, galleryCmd, imageGalleryCmd, audioGalleryCmd, videoPrefillCmd ]
            )

        UpdateTextInput text ->
            let
                uiState =
                    model.uiState
            in
            ( { model | uiState = { uiState | textInput = text } }, Cmd.none )

        GenerateScene ->
            let
                uiState =
                    model.uiState
            in
            ( { model
                | uiState =
                    { uiState
                        | isGenerating = True
                        , errorMessage = Nothing
                    }
              }
            , generateSceneRequest model.uiState.textInput
            )

        SceneGenerated sceneJson ->
            case Decode.decodeValue sceneDecoder sceneJson of
                Ok newScene ->
                    let
                        uiState =
                            model.uiState
                    in
                    ( { model
                        | scene = newScene
                        , initialScene = Just newScene
                        , uiState =
                            { uiState
                                | isGenerating = False
                                , textInput = ""
                            }
                      }
                    , Cmd.none
                    )

                Err error ->
                    let
                        uiState =
                            model.uiState
                    in
                    ( { model
                        | uiState =
                            { uiState
                                | isGenerating = False
                                , errorMessage = Just (Decode.errorToString error)
                            }
                      }
                    , Cmd.none
                    )

        SceneGeneratedResult result ->
            case result of
                Ok scene ->
                    let
                        uiState =
                            model.uiState
                        modelWithHistory =
                            saveToHistory model
                    in
                    ( { modelWithHistory
                        | scene = scene
                        , initialScene = Just scene
                        , uiState =
                            { uiState
                                | isGenerating = False
                                , textInput = ""
                            }
                      }
                    , sendSceneToThreeJs (sceneEncoder scene)
                    )

                Err error ->
                    let
                        uiState =
                            model.uiState

                        errorMessage =
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
                    in
                    ( { model
                        | uiState =
                            { uiState
                                | isGenerating = False
                                , errorMessage = Just errorMessage
                            }
                      }
                    , Cmd.none
                    )

        ObjectClicked objectId ->
            let
                scene =
                    model.scene
            in
            ( { model | scene = { scene | selectedObject = Just objectId } }
            , sendSelectionToThreeJs objectId
            )

        UpdateObjectTransform objectId newTransform ->
            let
                scene =
                    model.scene

                updateObject obj =
                    if obj.id == objectId then
                        { obj | transform = newTransform }
                    else
                        obj
            in
            ( { model
                | scene =
                    { scene
                        | objects = Dict.map (\_ obj -> updateObject obj) scene.objects
                    }
              }
            , Cmd.none
            )

        UpdateObjectProperty objectId propertyName value ->
            let
                scene =
                    model.scene

                updateObject obj =
                    if obj.id == objectId then
                        { obj | physicsProperties = updatePhysicsProperty obj.physicsProperties propertyName value }
                    else
                        obj

                updatePhysicsProperty props propName propValue =
                    case propName of
                        "mass" ->
                            { props | mass = propValue }

                        "friction" ->
                            { props | friction = propValue }

                        "restitution" ->
                            { props | restitution = propValue }

                        _ ->
                            props

                updatedScene =
                    { scene
                        | objects = Dict.map (\_ obj -> updateObject obj) scene.objects
                    }

                modelWithHistory =
                    saveToHistory model
            in
            ( { modelWithHistory | scene = updatedScene }
            , sendSceneToThreeJs (sceneEncoder updatedScene)
            )

        UpdateObjectDescription objectId desc ->
            let
                scene =
                    model.scene

                updateObject obj =
                    if obj.id == objectId then
                        { obj | description = if String.isEmpty desc then Nothing else Just desc }
                    else
                        obj

                updatedScene =
                    { scene
                        | objects = Dict.map (\_ obj -> updateObject obj) scene.objects
                    }

                modelWithHistory =
                    saveToHistory model
            in
            ( { modelWithHistory | scene = updatedScene }
            , sendSceneToThreeJs (sceneEncoder updatedScene)
            )

        ToggleSimulation ->
            let
                simulationState =
                    model.simulationState

                newIsRunning =
                    not simulationState.isRunning

                command =
                    if newIsRunning then
                        "start"
                    else
                        "pause"
            in
            ( { model
                | simulationState =
                    { simulationState
                        | isRunning = newIsRunning
                    }
              }
            , sendSimulationCommand command
            )

        ResetSimulation ->
            case model.initialScene of
                Just initial ->
                    ( { model | scene = initial }, sendSimulationCommand "reset" )

                Nothing ->
                    ( model, Cmd.none )

        SetTransformMode mode ->
            let
                simulationState =
                    model.simulationState

                modeString =
                    case mode of
                        Translate ->
                            "translate"

                        Rotate ->
                            "rotate"

                        Scale ->
                            "scale"
            in
            ( { model
                | simulationState =
                    { simulationState | transformMode = mode }
              }
            , sendTransformModeToThreeJs modeString
            )

        ClearError ->
            let
                uiState =
                    model.uiState
            in
            ( { model | uiState = { uiState | errorMessage = Nothing } }, Cmd.none )

        SelectionChanged maybeObjectId ->
            let
                scene =
                    model.scene
            in
            ( { model | scene = { scene | selectedObject = maybeObjectId } }, Cmd.none )

        TransformUpdated { objectId, transform } ->
            let
                scene =
                    model.scene

                updateObject obj =
                    if obj.id == objectId then
                        { obj | transform = transform }
                    else
                        obj
            in
            ( { model
                | scene =
                    { scene
                        | objects = Dict.map (\_ obj -> updateObject obj) scene.objects
                    }
              }
            , Cmd.none
            )

        UpdateRefineInput text ->
            let
                uiState = model.uiState
            in
            ( { model | uiState = { uiState | refineInput = text } }, Cmd.none )

        RefineScene ->
            let
                uiState = model.uiState
            in
            ( { model | uiState = { uiState | isRefining = True } }
            , refineSceneRequest model.scene model.uiState.refineInput
            )

        SceneRefined result ->
            case result of
                Ok newScene ->
                    let
                        uiState = model.uiState
                    in
                    ( { model
                        | scene = newScene
                        , history = model.scene :: model.history
                        , future = []
                        , uiState = { uiState | isRefining = False }
                      }
                    , Cmd.none
                    )

                Err error ->
                    let
                        uiState = model.uiState

                        errorMessage =
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
                    in
                    ( { model | uiState = { uiState | isRefining = False, errorMessage = Just errorMessage } }
                    , Cmd.none
                    )

        Undo ->
            case model.history of
                prevScene :: restHistory ->
                    ( { model | scene = prevScene, history = restHistory, future = model.scene :: model.future }
                    , Cmd.none
                    )

                [] ->
                    ( model, Cmd.none )

        Redo ->
            case model.future of
                nextScene :: restFuture ->
                    ( { model | scene = nextScene, future = restFuture, history = model.scene :: model.history }
                    , Cmd.none
                    )

                [] ->
                    ( model, Cmd.none )

        SaveScene ->
            ( model, Cmd.none )

        LoadScene ->
            ( model, Cmd.none )

        SceneLoadedFromStorage result ->
            ( model, Cmd.none )

        KeyDown key ->
            case key of
                "Control" ->
                    ( { model | ctrlPressed = True }, Cmd.none )

                _ ->
                    ( model, Cmd.none )

        KeyUp key ->
            case key of
                "Control" ->
                    ( { model | ctrlPressed = False }, Cmd.none )

                _ ->
                    ( model, Cmd.none )

        VideoMsg videoMsg ->
            let
                ( updatedVideoModel, videoCmd ) =
                    Video.update videoMsg model.videoModel

                -- Handle navigation to video detail page
                navCmd =
                    case videoMsg of
                        Video.NavigateToVideo videoId ->
                            Nav.pushUrl model.key (Route.toHref (Route.VideoDetail videoId))

                        _ ->
                            Cmd.none
            in
            ( { model | videoModel = updatedVideoModel }
            , Cmd.batch [ Cmd.map VideoMsg videoCmd, navCmd ]
            )

        VideoDetailMsg videoDetailMsg ->
            case model.videoDetailModel of
                Just videoDetailModel ->
                    let
                        ( updatedVideoDetailModel, videoDetailCmd ) =
                            VideoDetail.update videoDetailMsg videoDetailModel
                    in
                    ( { model | videoDetailModel = Just updatedVideoDetailModel }
                    , Cmd.map VideoDetailMsg videoDetailCmd
                    )

                Nothing ->
                    ( model, Cmd.none )

        GalleryMsg galleryMsg ->
            let
                ( updatedGalleryModel, galleryCmd ) =
                    VideoGallery.update galleryMsg model.galleryModel
            in
            ( { model | galleryModel = updatedGalleryModel }, Cmd.map GalleryMsg galleryCmd )

        SimulationGalleryMsg simulationGalleryMsg ->
            let
                ( updatedSimulationGalleryModel, simulationGalleryCmd ) =
                    SimulationGallery.update simulationGalleryMsg model.simulationGalleryModel
            in
            ( { model | simulationGalleryModel = updatedSimulationGalleryModel }, Cmd.map SimulationGalleryMsg simulationGalleryCmd )

        ImageMsg imageMsg ->
            let
                ( updatedImageModel, imageCmd ) =
                    Image.update imageMsg model.imageModel

                -- Handle navigation to image detail page
                navCmd =
                    case imageMsg of
                        Image.NavigateToImage imageId ->
                            Nav.pushUrl model.key (Route.toHref (Route.ImageDetail imageId))

                        _ ->
                            Cmd.none
            in
            ( { model | imageModel = updatedImageModel }
            , Cmd.batch [ Cmd.map ImageMsg imageCmd, navCmd ]
            )

        ImageDetailMsg imageDetailMsg ->
            case model.imageDetailModel of
                Just imageDetailModel ->
                    let
                        ( updatedImageDetailModel, imageDetailCmd ) =
                            ImageDetail.update imageDetailMsg imageDetailModel
                    in
                    ( { model | imageDetailModel = Just updatedImageDetailModel }
                    , Cmd.map ImageDetailMsg imageDetailCmd
                    )

                Nothing ->
                    ( model, Cmd.none )

        ImageGalleryMsg imageGalleryMsg ->
            let
                ( updatedImageGalleryModel, imageGalleryCmd ) =
                    ImageGallery.update imageGalleryMsg model.imageGalleryModel

                -- Handle navigation to video page with image
                ( navCmd, updatedModel ) =
                    case imageGalleryMsg of
                        ImageGallery.CreateVideoFromImage modelId imageUrl ->
                            -- Store the model ID and image URL, then navigate to videos page
                            ( Nav.pushUrl model.key "/videos"
                            , { model
                                | imageGalleryModel = updatedImageGalleryModel
                                , pendingVideoFromImage = Just { modelId = modelId, imageUrl = imageUrl }
                              }
                            )

                        _ ->
                            ( Cmd.none
                            , { model | imageGalleryModel = updatedImageGalleryModel }
                            )
            in
            ( updatedModel, Cmd.batch [ Cmd.map ImageGalleryMsg imageGalleryCmd, navCmd ] )

        AudioMsg audioMsg ->
            let
                ( updatedAudioModel, audioCmd ) =
                    Audio.update audioMsg model.audioModel

                -- Handle navigation to audio detail page
                navCmd =
                    case audioMsg of
                        Audio.NavigateToAudio audioId ->
                            Nav.pushUrl model.key (Route.toHref (Route.AudioDetail audioId))

                        _ ->
                            Cmd.none
            in
            ( { model | audioModel = updatedAudioModel }
            , Cmd.batch [ Cmd.map AudioMsg audioCmd, navCmd ]
            )

        AudioDetailMsg audioDetailMsg ->
            case model.audioDetailModel of
                Just audioDetailModel ->
                    let
                        ( updatedAudioDetailModel, audioDetailCmd ) =
                            AudioDetail.update audioDetailMsg audioDetailModel
                    in
                    ( { model | audioDetailModel = Just updatedAudioDetailModel }
                    , Cmd.map AudioDetailMsg audioDetailCmd
                    )

                Nothing ->
                    ( model, Cmd.none )

        AudioGalleryMsg audioGalleryMsg ->
            let
                ( updatedAudioGalleryModel, audioGalleryCmd ) =
                    AudioGallery.update audioGalleryMsg model.audioGalleryModel
            in
            ( { model | audioGalleryModel = updatedAudioGalleryModel }, Cmd.map AudioGalleryMsg audioGalleryCmd )

        AuthMsg authMsg ->
            let
                ( updatedAuthModel, authCmd ) =
                    Auth.update authMsg model.authModel

                -- Trigger gallery fetches when login succeeds (cookies are already set by server)
                fetchCmd =
                    case authMsg of
                        Auth.LoginResult (Ok _) ->
                            Cmd.batch
                                [ Cmd.map GalleryMsg (Task.perform (always VideoGallery.FetchVideos) (Task.succeed ()))
                                , Cmd.map SimulationGalleryMsg (Task.perform (always SimulationGallery.FetchVideos) (Task.succeed ()))
                                , Cmd.map ImageGalleryMsg (Task.perform (always ImageGallery.FetchImages) (Task.succeed ()))
                                , Cmd.map AudioGalleryMsg (Task.perform (always AudioGallery.FetchAudio) (Task.succeed ()))
                                ]

                        _ ->
                            Cmd.none
            in
            ( { model | authModel = updatedAuthModel }
            , Cmd.batch [ Cmd.map AuthMsg authCmd, fetchCmd ]
            )

        CreativeBriefEditorMsg briefMsg ->
            let
                ( updatedModel, cmd ) =
                    CreativeBriefEditor.update briefMsg model.creativeBriefEditorModel
            in
            ( { model | creativeBriefEditorModel = updatedModel }
            , Cmd.map CreativeBriefEditorMsg cmd
            )

        BriefGalleryMsg galleryMsg ->
            let
                ( updatedModel, cmd ) =
                    BriefGallery.update galleryMsg model.briefGalleryModel
            in
            ( { model | briefGalleryModel = updatedModel }
            , Cmd.map BriefGalleryMsg cmd
            )

        NavigateTo route ->
            ( model, Nav.pushUrl model.key (Route.toHref route) )


-- HISTORY MANAGEMENT


saveToHistory : Model -> Model
saveToHistory model =
    { model
        | history = model.scene :: List.take 49 model.history  -- Keep last 50 states
        , future = []  -- Clear future when new change is made
    }


-- VIEW


view : Model -> Browser.Document Msg
view model =
    { title = "Gauntlet Video Sim POC"
    , body =
        case model.authModel.loginState of
            Auth.Checking ->
                -- Show blurred page with loading spinner
                [ div [ style "position" "relative" ]
                    [ div [ style "filter" "blur(4px)", style "pointer-events" "none" ]
                        [ viewMainContent model ]
                    , div
                        [ style "position" "fixed"
                        , style "top" "0"
                        , style "left" "0"
                        , style "width" "100%"
                        , style "height" "100%"
                        , style "display" "flex"
                        , style "align-items" "center"
                        , style "justify-content" "center"
                        , style "background" "rgba(0, 0, 0, 0.3)"
                        , style "z-index" "9999"
                        ]
                        [ div
                            [ style "width" "60px"
                            , style "height" "60px"
                            , style "border" "6px solid #f3f3f3"
                            , style "border-top" "6px solid #667eea"
                            , style "border-radius" "50%"
                            , style "animation" "spin 1s linear infinite"
                            ]
                            []
                        ]
                    ]
                ]

            Auth.NotLoggedIn ->
                -- Show login screen
                [ Html.map AuthMsg (Auth.view model.authModel) ]

            Auth.LoggingIn ->
                -- Show login screen while logging in
                [ Html.map AuthMsg (Auth.view model.authModel) ]

            Auth.LoggedIn ->
                -- Show normal page
                [ viewMainContent model ]
    }


viewMainContent : Model -> Html Msg
viewMainContent model =
    div []
        [ viewTabs model
        , case model.route of
            Just Route.Physics ->
                div [ class "app-container" ]
                    [ viewLeftPanel model
                    , viewCanvasContainer
                    , viewRightPanel model
                    , viewBottomBar model
                    ]

            Just Route.Videos ->
                Video.view model.videoModel
                    |> Html.map VideoMsg

            Just (Route.VideoDetail _) ->
                case model.videoDetailModel of
                    Just videoDetailModel ->
                        VideoDetail.view videoDetailModel
                            |> Html.map VideoDetailMsg

                    Nothing ->
                        div [ class "loading" ] [ text "Loading video detail..." ]

            Just Route.Gallery ->
                VideoGallery.view model.galleryModel
                    |> Html.map GalleryMsg

            Just Route.SimulationGallery ->
                SimulationGallery.view model.simulationGalleryModel
                    |> Html.map SimulationGalleryMsg

            Just Route.Images ->
                Image.view model.imageModel
                    |> Html.map ImageMsg

            Just (Route.ImageDetail _) ->
                case model.imageDetailModel of
                    Just imageDetailModel ->
                        ImageDetail.view imageDetailModel
                            |> Html.map ImageDetailMsg

                    Nothing ->
                        div [ class "loading" ] [ text "Loading image detail..." ]

            Just Route.ImageGallery ->
                ImageGallery.view model.imageGalleryModel
                    |> Html.map ImageGalleryMsg

            Just Route.Audio ->
                Audio.view model.audioModel
                    |> Html.map AudioMsg

            Just (Route.AudioDetail _) ->
                case model.audioDetailModel of
                    Just audioDetailModel ->
                        AudioDetail.view audioDetailModel
                            |> Html.map AudioDetailMsg

                    Nothing ->
                        div [ class "loading" ] [ text "Loading audio detail..." ]

            Just Route.AudioGallery ->
                AudioGallery.view model.audioGalleryModel
                    |> Html.map AudioGalleryMsg

            Just Route.Auth ->
                Html.map AuthMsg (Auth.view model.authModel)

            Just Route.BriefGallery ->
                BriefGallery.view model.briefGalleryModel
                    |> Html.map BriefGalleryMsg

            Just Route.CreativeBriefEditor ->
                CreativeBriefEditor.view model.creativeBriefEditorModel
                    |> Html.map CreativeBriefEditorMsg

            Nothing ->
                div [ class "app-container" ]
                    [ viewLeftPanel model
                    , viewCanvasContainer
                    , viewRightPanel model
                    , viewBottomBar model
                    ]
        ]


viewTabs : Model -> Html Msg
viewTabs model =
    div [ class "tabs" ]
        [ a
            [ href "/videos"
            , class (if model.route == Just Route.Videos then "active" else "")
            ]
            [ text "Video Models" ]
        , a
            [ href "/gallery"
            , class (if model.route == Just Route.Gallery then "active" else "")
            ]
            [ text "Video Gallery" ]
        , a
            [ href "/images"
            , class (if model.route == Just Route.Images then "active" else "")
            ]
            [ text "Image Models" ]
        , a
            [ href "/image-gallery"
            , class (if model.route == Just Route.ImageGallery then "active" else "")
            ]
            [ text "Image Gallery" ]
        , a
            [ href "/audio"
            , class (if model.route == Just Route.Audio then "active" else "")
            ]
            [ text "Audio Models" ]
        , a
            [ href "/audio-gallery"
            , class (if model.route == Just Route.AudioGallery then "active" else "")
            ]
            [ text "Audio Gallery" ]
        , a
            [ href "/simulations"
            , class (if model.route == Just Route.SimulationGallery then "active" else "")
            ]
            [ text "Simulation Gallery" ]
        , a
            [ href "/physics"
            , class (if model.route == Just Route.Physics then "active" else "")
            ]
            [ text "Physics Simulator" ]
        , a
            [ href "/auth"
            , class (if model.route == Just Route.Auth then "active" else "")
            ]
            [ text "Auth" ]
        , a
            [ href "/briefs"
            , class (if model.route == Just Route.BriefGallery then "active" else "")
            ]
            [ text "Brief Gallery" ]
        , a
            [ href "/creative"
            , class (if model.route == Just Route.CreativeBriefEditor then "active" else "")
            ]
            [ text "Creative Brief Editor" ]
        ]


viewBottomBar : Model -> Html Msg
viewBottomBar model =
    div [ class "bottom-bar" ]
        [ div [ class "simulation-controls" ]
            [ button
                [ onClick ToggleSimulation
                , class (if model.simulationState.isRunning then "active" else "")
                ]
                [ text (if model.simulationState.isRunning then "Pause" else "Play") ]
            , button [ onClick ResetSimulation ] [ text "Reset" ]
            ]
        , div [ class "transform-controls" ]
            [ button
                [ onClick (SetTransformMode Translate)
                , class (if model.simulationState.transformMode == Translate then "active" else "")
                ]
                [ text "Move (G)" ]
            , button
                [ onClick (SetTransformMode Rotate)
                , class (if model.simulationState.transformMode == Rotate then "active" else "")
                ]
                [ text "Rotate (R)" ]
            , button
                [ onClick (SetTransformMode Scale)
                , class (if model.simulationState.transformMode == Scale then "active" else "")
                ]
                [ text "Scale (S)" ]
            ]
        , div [ class "history-controls" ]
            [ button
                [ onClick Undo
                , disabled (List.isEmpty model.history)
                ]
                [ text "Undo" ]
            , button
                [ onClick Redo
                , disabled (List.isEmpty model.future)
                ]
                [ text "Redo" ]
            , button [ onClick SaveScene ] [ text "Save" ]
            , button [ onClick LoadScene ] [ text "Load" ]
            ]
        ]


viewLeftPanel : Model -> Html Msg
viewLeftPanel model =
    div [ class "left-panel" ]
        [ h2 [] [ text "Generation" ]
        , textarea
            [ placeholder "Describe a scene to generate..."
            , value model.uiState.textInput
            , onInput UpdateTextInput
            , disabled model.uiState.isGenerating
            ]
            []
        , button
            [ onClick GenerateScene
            , disabled (String.isEmpty (String.trim model.uiState.textInput) || model.uiState.isGenerating)
            ]
            [ if model.uiState.isGenerating then
                span [ class "loading" ] []
              else
                text ""
            , text (if model.uiState.isGenerating then "Generating..." else "Generate Scene")
            ]
        , case model.uiState.errorMessage of
            Just error ->
                div [ class "error" ]
                    [ text error
                    , button [ onClick ClearError ] [ text "×" ]
                    ]

            Nothing ->
                text ""
        , h2 [] [ text "Refinement" ]
        , textarea
            [ placeholder "Describe how to modify the current scene..."
            , value model.uiState.refineInput
            , onInput UpdateRefineInput
            , disabled (Dict.isEmpty model.scene.objects || model.uiState.isRefining)
            ]
            []
        , button
            [ onClick RefineScene
            , disabled (String.isEmpty (String.trim model.uiState.refineInput) || Dict.isEmpty model.scene.objects || model.uiState.isRefining)
            ]
            [ if model.uiState.isRefining then
                span [ class "loading" ] []
              else
                text ""
            , text (if model.uiState.isRefining then "Refining..." else "Refine Scene")
            ]
        ]


viewCanvasContainer : Html Msg
viewCanvasContainer =
    div [ id "canvas-container", class "canvas-container" ]
        []


viewRightPanel : Model -> Html Msg
viewRightPanel model =
    div [ class "right-panel" ]
        [ h2 [] [ text "Properties" ]
        , case model.scene.selectedObject of
            Just objectId ->
                case Dict.get objectId model.scene.objects of
                    Just object ->
                        viewObjectProperties object

                    Nothing ->
                        text "Object not found"

            Nothing ->
                text "No object selected"
        ]


viewObjectProperties : PhysicsObject -> Html Msg
viewObjectProperties object =
    div []
        [ h3 [] [ text ("Object: " ++ object.id) ]
        , div [ class "property-section" ]
            [ h4 [] [ text "Transform" ]
            , viewVec3Input "Position" object.transform.position (\vec -> UpdateObjectTransform object.id { position = vec, rotation = object.transform.rotation, scale = object.transform.scale })
            , viewVec3Input "Rotation" object.transform.rotation (\vec -> UpdateObjectTransform object.id { position = object.transform.position, rotation = vec, scale = object.transform.scale })
            , viewVec3Input "Scale" object.transform.scale (\vec -> UpdateObjectTransform object.id { position = object.transform.position, rotation = object.transform.rotation, scale = vec })
            ]
        , div [ class "property-section" ]
            [ h4 [] [ text "Physics" ]
            , viewFloatInput "Mass" object.physicsProperties.mass (\val -> UpdateObjectProperty object.id "mass" val)
            , viewFloatInput "Friction" object.physicsProperties.friction (\val -> UpdateObjectProperty object.id "friction" val)
            , viewFloatInput "Restitution" object.physicsProperties.restitution (\val -> UpdateObjectProperty object.id "restitution" val)
            ]
        , div [ class "property-section" ]
            [ h4 [] [ text "Visual" ]
            , div [] [ text ("Color: " ++ object.visualProperties.color) ]
            , div [] [ text ("Shape: " ++ shapeToString object.visualProperties.shape) ]
            ]
        , div [ class "property-section" ]
            [ h4 [] [ text "Description (for Genesis)" ]
            , div [ class "description-help" ]
                [ text "Describe what this object should look like (e.g., 'blue corvette', 'wooden table')" ]
            , textarea
                [ class "description-input"
                , placeholder "e.g., blue corvette, light pole, wooden coffee table..."
                , Html.Attributes.value (Maybe.withDefault "" object.description)
                , onInput (\desc -> UpdateObjectDescription object.id desc)
                , rows 3
                ]
                []
            ]
        ]


viewVec3Input : String -> Vec3 -> (Vec3 -> Msg) -> Html Msg
viewVec3Input labelText vec3 msgConstructor =
    div [ class "vec3-input" ]
        [ div [] [ text labelText ]
        , div [ class "input-row" ]
            [ input
                [ type_ "number"
                , step "0.1"
                , Html.Attributes.value (String.fromFloat vec3.x)
                , onInput (\x -> msgConstructor { vec3 | x = Maybe.withDefault vec3.x (String.toFloat x) })
                ]
                []
            , input
                [ type_ "number"
                , step "0.1"
                , Html.Attributes.value (String.fromFloat vec3.y)
                , onInput (\y -> msgConstructor { vec3 | y = Maybe.withDefault vec3.y (String.toFloat y) })
                ]
                []
            , input
                [ type_ "number"
                , step "0.1"
                , Html.Attributes.value (String.fromFloat vec3.z)
                , onInput (\z -> msgConstructor { vec3 | z = Maybe.withDefault vec3.z (String.toFloat z) })
                ]
                []
            ]
        ]


viewFloatInput : String -> Float -> (Float -> Msg) -> Html Msg
viewFloatInput labelText value msgConstructor =
    div [ class "float-input" ]
        [ div [] [ text labelText ]
        , input
            [ type_ "number"
            , step "0.1"
            , Html.Attributes.value (String.fromFloat value)
            , onInput (\val -> msgConstructor (Maybe.withDefault value (String.toFloat val)))
            ]
            []
        ]


shapeToString : Shape -> String
shapeToString shape =
    case shape of
        Box ->
            "Box"

        Sphere ->
            "Sphere"

        Cylinder ->
            "Cylinder"


-- SUBSCRIPTIONS


subscriptions : Model -> Sub Msg
subscriptions model =
    let
        gallerySub =
            case model.route of
                Just Route.Gallery ->
                    Sub.map GalleryMsg (VideoGallery.subscriptions model.galleryModel)

                _ ->
                    Sub.none

        simulationGallerySub =
            case model.route of
                Just Route.SimulationGallery ->
                    Sub.map SimulationGalleryMsg (SimulationGallery.subscriptions model.simulationGalleryModel)

                _ ->
                    Sub.none

        videoDetailSub =
            case ( model.route, model.videoDetailModel ) of
                ( Just (Route.VideoDetail _), Just videoDetailModel ) ->
                    Sub.map VideoDetailMsg (VideoDetail.subscriptions videoDetailModel)

                _ ->
                    Sub.none

        imageGallerySub =
            case model.route of
                Just Route.ImageGallery ->
                    Sub.map ImageGalleryMsg (ImageGallery.subscriptions model.imageGalleryModel)

                _ ->
                    Sub.none

        imageDetailSub =
            case ( model.route, model.imageDetailModel ) of
                ( Just (Route.ImageDetail _), Just imageDetailModel ) ->
                    Sub.map ImageDetailMsg (ImageDetail.subscriptions imageDetailModel)

                _ ->
                    Sub.none

        audioGallerySub =
            case model.route of
                Just Route.AudioGallery ->
                    Sub.map AudioGalleryMsg (AudioGallery.subscriptions model.audioGalleryModel)

                _ ->
                    Sub.none

        audioDetailSub =
            case ( model.route, model.audioDetailModel ) of
                ( Just (Route.AudioDetail _), Just audioDetailModel ) ->
                    Sub.map AudioDetailMsg (AudioDetail.subscriptions audioDetailModel)

                _ ->
                    Sub.none

        creativeBriefEditorSub =
            case model.route of
                Just Route.CreativeBriefEditor ->
                    Sub.map CreativeBriefEditorMsg (CreativeBriefEditor.subscriptions model.creativeBriefEditorModel)

                _ ->
                    Sub.none

        briefGallerySub =
            case model.route of
                Just Route.BriefGallery ->
                    Sub.map BriefGalleryMsg (BriefGallery.subscriptions model.briefGalleryModel)

                _ ->
                    Sub.none
    in
    Sub.batch
        [ sendSelectionToElm SelectionChanged
        , sendTransformUpdateToElm TransformUpdated
        , sceneLoadedFromStorage SceneLoadedFromStorage
        , Browser.Events.onKeyDown (Decode.map KeyDown keyDecoder)
        , Browser.Events.onKeyUp (Decode.map KeyUp keyDecoder)
        , gallerySub
        , simulationGallerySub
        , videoDetailSub
        , imageGallerySub
        , imageDetailSub
        , audioGallerySub
        , audioDetailSub
        , creativeBriefEditorSub
        , briefGallerySub
        ]


keyDecoder : Decode.Decoder String
keyDecoder =
    Decode.field "key" Decode.string


-- PORTS


port sendSceneToThreeJs : Encode.Value -> Cmd msg


port sendSelectionToThreeJs : String -> Cmd msg


port sendSimulationCommand : String -> Cmd msg


port sendSelectionToElm : (Maybe String -> msg) -> Sub msg


port sendTransformModeToThreeJs : String -> Cmd msg


port sendTransformUpdateToElm : ({ objectId : String, transform : Transform } -> msg) -> Sub msg


port saveSceneToStorage : Encode.Value -> Cmd msg


port loadSceneFromStorage : () -> Cmd msg


port sceneLoadedFromStorage : (Encode.Value -> msg) -> Sub msg


-- DECODERS


sceneDecoder : Decode.Decoder Scene
sceneDecoder =
    Decode.map2 Scene
        (Decode.field "objects" (Decode.dict physicsObjectDecoder))
        (Decode.maybe (Decode.field "selectedObject" Decode.string))


physicsObjectDecoder : Decode.Decoder PhysicsObject
physicsObjectDecoder =
    Decode.map5 PhysicsObject
        (Decode.field "id" Decode.string)
        (Decode.field "transform" transformDecoder)
        (Decode.field "physicsProperties" physicsPropertiesDecoder)
        (Decode.field "visualProperties" visualPropertiesDecoder)
        (Decode.maybe (Decode.field "description" Decode.string))


transformDecoder : Decode.Decoder Transform
transformDecoder =
    Decode.map3 Transform
        (Decode.field "position" vec3Decoder)
        (Decode.field "rotation" vec3Decoder)
        (Decode.field "scale" vec3Decoder)


vec3Decoder : Decode.Decoder Vec3
vec3Decoder =
    Decode.map3 Vec3
        (Decode.field "x" Decode.float)
        (Decode.field "y" Decode.float)
        (Decode.field "z" Decode.float)


physicsPropertiesDecoder : Decode.Decoder PhysicsProperties
physicsPropertiesDecoder =
    Decode.map3 PhysicsProperties
        (Decode.field "mass" Decode.float)
        (Decode.field "friction" Decode.float)
        (Decode.field "restitution" Decode.float)


visualPropertiesDecoder : Decode.Decoder VisualProperties
visualPropertiesDecoder =
    Decode.map2 VisualProperties
        (Decode.field "color" Decode.string)
        (Decode.field "shape" shapeDecoder)


shapeDecoder : Decode.Decoder Shape
shapeDecoder =
    Decode.string
        |> Decode.andThen
            (\shapeStr ->
                case shapeStr of
                    "Box" ->
                        Decode.succeed Box

                    "Sphere" ->
                        Decode.succeed Sphere

                    "Cylinder" ->
                        Decode.succeed Cylinder

                    _ ->
                        Decode.fail ("Unknown shape: " ++ shapeStr)
            )


-- HTTP REQUESTS


generateSceneRequest : String -> Cmd Msg
generateSceneRequest prompt =
    -- Cookies are sent automatically, no need for Authorization header
    Http.post
        { url = "/api/generate"
        , body = Http.jsonBody (Encode.object [ ( "prompt", Encode.string prompt ) ])
        , expect = Http.expectJson SceneGeneratedResult sceneDecoder
        }


refineSceneRequest : Scene -> String -> Cmd Msg
refineSceneRequest scene prompt =
    -- Cookies are sent automatically, no need for Authorization header
    Http.post
        { url = "/api/refine"
        , body = Http.jsonBody (Encode.object [ ( "scene", sceneEncoder scene ), ( "prompt", Encode.string prompt ) ])
        , expect = Http.expectJson SceneRefined sceneDecoder
        }


-- ENCODERS


sceneEncoder : Scene -> Encode.Value
sceneEncoder scene =
    Encode.object
        [ ( "objects", Encode.dict identity physicsObjectEncoder scene.objects )
        , ( "selectedObject", maybeEncoder Encode.string scene.selectedObject )
        ]


physicsObjectEncoder : PhysicsObject -> Encode.Value
physicsObjectEncoder obj =
    let
        baseFields =
            [ ( "id", Encode.string obj.id )
            , ( "transform", transformEncoder obj.transform )
            , ( "physicsProperties", physicsPropertiesEncoder obj.physicsProperties )
            , ( "visualProperties", visualPropertiesEncoder obj.visualProperties )
            ]

        descriptionField =
            case obj.description of
                Just desc ->
                    [ ( "description", Encode.string desc ) ]

                Nothing ->
                    []
    in
    Encode.object (baseFields ++ descriptionField)


transformEncoder : Transform -> Encode.Value
transformEncoder transform =
    Encode.object
        [ ( "position", vec3Encoder transform.position )
        , ( "rotation", vec3Encoder transform.rotation )
        , ( "scale", vec3Encoder transform.scale )
        ]


vec3Encoder : Vec3 -> Encode.Value
vec3Encoder vec3 =
    Encode.object
        [ ( "x", Encode.float vec3.x )
        , ( "y", Encode.float vec3.y )
        , ( "z", Encode.float vec3.z )
        ]


physicsPropertiesEncoder : PhysicsProperties -> Encode.Value
physicsPropertiesEncoder props =
    Encode.object
        [ ( "mass", Encode.float props.mass )
        , ( "friction", Encode.float props.friction )
        , ( "restitution", Encode.float props.restitution )
        ]


visualPropertiesEncoder : VisualProperties -> Encode.Value
visualPropertiesEncoder props =
    Encode.object
        [ ( "color", Encode.string props.color )
        , ( "shape", shapeEncoder props.shape )
        ]


shapeEncoder : Shape -> Encode.Value
shapeEncoder shape =
    Encode.string <|
        case shape of
            Box ->
                "Box"

            Sphere ->
                "Sphere"

            Cylinder ->
                "Cylinder"


maybeEncoder : (a -> Encode.Value) -> Maybe a -> Encode.Value
maybeEncoder encoder maybeValue =
    case maybeValue of
        Just value ->
            encoder value

        Nothing ->
            Encode.null
