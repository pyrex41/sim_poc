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
import Set exposing (Set)
import Url exposing (Url)
import Video
import VideoGallery
import SimulationGallery


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
    , galleryModel : VideoGallery.Model
    , simulationGalleryModel : SimulationGallery.Model
    }


type alias Scene =
    { objects : Dict String PhysicsObject
    , selectedObject : Maybe String
    , selectedObjects : Set String
    , sceneContext : SceneContext
    }


type alias SceneContext =
    { environment : EnvironmentSettings
    , narrative : String
    , lighting : LightingSettings
    , renderQuality : String
    }


type alias EnvironmentSettings =
    { timeOfDay : String
    , weather : String
    , season : String
    , atmosphere : Float
    }


type alias LightingSettings =
    { ambientIntensity : Float
    , ambientColor : String
    , directionalIntensity : Float
    , directionalColor : String
    , directionalAngle : Float
    , shadows : Bool
    }


type alias MotionData =
    { animations : Dict String Encode.Value
    , cameraAnimation : Encode.Value
    , description : String
    }


type alias UiState =
    { textInput : String
    , isGenerating : Bool
    , errorMessage : Maybe String
    , refineInput : String
    , isRefining : Bool
    , populateInput : String
    , isPopulating : Bool
    , populateNumObjects : Int
    , populatePlacementStrategy : String
    , motionInput : String
    , isGeneratingMotion : Bool
    , motionData : Maybe MotionData
    }


type alias SimulationState =
    { isRunning : Bool
    , transformMode : TransformMode
    , snapToGrid : Bool
    , gridSize : Float
    , shiftPressed : Bool
    , typingInInput : Bool
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


defaultSceneContext : SceneContext
defaultSceneContext =
    { environment =
        { timeOfDay = "midday"
        , weather = "clear"
        , season = "summer"
        , atmosphere = 0.5
        }
    , narrative = ""
    , lighting =
        { ambientIntensity = 0.4
        , ambientColor = "#FFFFFF"
        , directionalIntensity = 0.8
        , directionalColor = "#FFFFCC"
        , directionalAngle = 45.0
        , shadows = True
        }
    , renderQuality = "high"
    }


init : () -> Url -> Nav.Key -> ( Model, Cmd Msg )
init _ url key =
    let
        ( videoModel, videoCmd ) =
            Video.init

        ( galleryModel, galleryCmd ) =
            VideoGallery.init

        ( simulationGalleryModel, simulationGalleryCmd ) =
            SimulationGallery.init

        route =
            Route.fromUrl url
    in
    ( { key = key
      , url = url
      , route = route
      , scene = { objects = Dict.empty, selectedObject = Nothing, selectedObjects = Set.empty, sceneContext = defaultSceneContext }
      , uiState = { textInput = "", isGenerating = False, errorMessage = Nothing, refineInput = "", isRefining = False, populateInput = "", isPopulating = False, populateNumObjects = 5, populatePlacementStrategy = "natural", motionInput = "", isGeneratingMotion = False, motionData = Nothing }
      , simulationState = { isRunning = False, transformMode = Translate, snapToGrid = False, gridSize = 1.0, shiftPressed = False, typingInInput = False }
      , initialScene = Nothing
      , history = []
      , future = []
      , ctrlPressed = False
      , videoModel = videoModel
      , galleryModel = galleryModel
      , simulationGalleryModel = simulationGalleryModel
      }
    , Cmd.batch
        [ Cmd.map VideoMsg videoCmd
        , Cmd.map GalleryMsg galleryCmd
        , Cmd.map SimulationGalleryMsg simulationGalleryCmd
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
    | UpdatePopulateInput String
    | UpdatePopulateNumObjects Int
    | UpdatePopulatePlacementStrategy String
    | PopulateScene
    | ScenePopulated (Result Http.Error Scene)
    | UpdateMotionInput String
    | GenerateMotion
    | MotionGenerated (Result Http.Error MotionData)
    | ToggleObjectSelection String
    | ClearSelection
    | DuplicateSelected
    | DeleteSelected
    | ToggleSnapToGrid
    | UpdateGridSize Float
    | ShiftKeyDown Bool
    | UpdateEnvironmentTimeOfDay String
    | UpdateEnvironmentWeather String
    | UpdateEnvironmentSeason String
    | UpdateEnvironmentAtmosphere Float
    | UpdateSceneNarrative String
    | UpdateAmbientIntensity Float
    | UpdateAmbientColor String
    | UpdateDirectionalIntensity Float
    | UpdateDirectionalColor String
    | UpdateDirectionalAngle Float
    | ToggleShadows
    | UpdateRenderQuality String
    | Undo
    | Redo
    | SaveScene
    | LoadScene
    | SceneLoadedFromStorage Encode.Value
    | KeyDown String
    | KeyUp String
    | InputFocused
    | InputBlurred
    | ClearError
    | SelectionChanged (Maybe String)
    | TransformUpdated { objectId : String, transform : Transform }
    | VideoMsg Video.Msg
    | GalleryMsg VideoGallery.Msg
    | SimulationGalleryMsg SimulationGallery.Msg


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
            ( { model | url = url, route = Route.fromUrl url }
            , Cmd.none
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

        UpdateRefineInput newInput ->
            let
                uiState =
                    model.uiState
            in
            ( { model | uiState = { uiState | refineInput = newInput } }, Cmd.none )

        RefineScene ->
            let
                uiState =
                    model.uiState
            in
            ( { model | uiState = { uiState | isRefining = True, errorMessage = Nothing } }
            , refineSceneRequest model.scene model.uiState.refineInput
            )

        SceneRefined result ->
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
                        , uiState =
                            { uiState
                                | isRefining = False
                                , refineInput = ""
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
                                | isRefining = False
                                , errorMessage = Just errorMessage
                            }
                      }
                    , Cmd.none
                    )

        UpdatePopulateInput text ->
            let
                uiState =
                    model.uiState
            in
            ( { model | uiState = { uiState | populateInput = text } }, Cmd.none )

        UpdatePopulateNumObjects num ->
            let
                uiState =
                    model.uiState
            in
            ( { model | uiState = { uiState | populateNumObjects = num } }, Cmd.none )

        UpdatePopulatePlacementStrategy strategy ->
            let
                uiState =
                    model.uiState
            in
            ( { model | uiState = { uiState | populatePlacementStrategy = strategy } }, Cmd.none )

        PopulateScene ->
            let
                uiState =
                    model.uiState
            in
            ( { model | uiState = { uiState | isPopulating = True, errorMessage = Nothing } }
            , populateSceneRequest model.scene model.uiState.populateInput model.uiState.populateNumObjects model.uiState.populatePlacementStrategy
            )

        ScenePopulated result ->
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
                        , uiState =
                            { uiState
                                | isPopulating = False
                                , populateInput = ""
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
                                | isPopulating = False
                                , errorMessage = Just errorMessage
                            }
                      }
                    , Cmd.none
                    )

        UpdateMotionInput text ->
            let
                uiState =
                    model.uiState
            in
            ( { model | uiState = { uiState | motionInput = text } }, Cmd.none )

        GenerateMotion ->
            let
                uiState =
                    model.uiState
            in
            ( { model | uiState = { uiState | isGeneratingMotion = True } }
            , generateMotionRequest model.scene.objects model.uiState.motionInput
            )

        MotionGenerated result ->
            case result of
                Ok motionData ->
                    let
                        uiState =
                            model.uiState
                    in
                    ( { model
                        | uiState =
                            { uiState
                                | isGeneratingMotion = False
                                , motionData = Just motionData
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
                                | isGeneratingMotion = False
                                , errorMessage = Just ("Motion generation failed")
                            }
                      }
                    , Cmd.none
                    )

        ToggleObjectSelection objectId ->
            let
                scene =
                    model.scene

                simulationState =
                    model.simulationState

                newSelectedObjects =
                    if simulationState.shiftPressed then
                        -- Multi-select with Shift
                        if Set.member objectId scene.selectedObjects then
                            Set.remove objectId scene.selectedObjects
                        else
                            Set.insert objectId scene.selectedObjects
                    else
                        -- Single select without Shift
                        Set.singleton objectId
            in
            ( { model
                | scene =
                    { scene
                        | selectedObject = Just objectId
                        , selectedObjects = newSelectedObjects
                    }
              }
            , sendSelectionToThreeJs objectId
            )

        ClearSelection ->
            let
                scene =
                    model.scene
            in
            ( { model
                | scene =
                    { scene
                        | selectedObject = Nothing
                        , selectedObjects = Set.empty
                    }
              }
            , Cmd.none
            )

        DuplicateSelected ->
            let
                scene =
                    model.scene

                selectedIds =
                    if Set.isEmpty scene.selectedObjects then
                        case scene.selectedObject of
                            Just id ->
                                [ id ]

                            Nothing ->
                                []
                    else
                        Set.toList scene.selectedObjects

                duplicateObject : String -> PhysicsObject -> ( String, PhysicsObject )
                duplicateObject oldId obj =
                    let
                        newId =
                            oldId ++ "_copy"

                        offsetPos =
                            obj.transform.position

                        newPos =
                            { offsetPos | x = offsetPos.x + 2.0 }
                    in
                    ( newId
                    , { obj
                        | id = newId
                        , transform =
                            { position = newPos
                            , rotation = obj.transform.rotation
                            , scale = obj.transform.scale
                            }
                      }
                    )

                newObjects =
                    selectedIds
                        |> List.filterMap (\id -> Dict.get id scene.objects |> Maybe.map (duplicateObject id))
                        |> Dict.fromList

                updatedObjects =
                    Dict.union newObjects scene.objects

                modelWithHistory =
                    saveToHistory model
            in
            ( { modelWithHistory
                | scene = { scene | objects = updatedObjects }
              }
            , sendSceneToThreeJs (sceneEncoder { scene | objects = updatedObjects })
            )

        DeleteSelected ->
            let
                scene =
                    model.scene

                selectedIds =
                    if Set.isEmpty scene.selectedObjects then
                        case scene.selectedObject of
                            Just id ->
                                Set.singleton id

                            Nothing ->
                                Set.empty
                    else
                        scene.selectedObjects

                updatedObjects =
                    Set.foldl Dict.remove scene.objects selectedIds

                modelWithHistory =
                    saveToHistory model
            in
            ( { modelWithHistory
                | scene =
                    { scene
                        | objects = updatedObjects
                        , selectedObject = Nothing
                        , selectedObjects = Set.empty
                    }
              }
            , sendSceneToThreeJs (sceneEncoder { scene | objects = updatedObjects })
            )

        ToggleSnapToGrid ->
            let
                simulationState =
                    model.simulationState
            in
            ( { model
                | simulationState = { simulationState | snapToGrid = not simulationState.snapToGrid }
              }
            , Cmd.none
            )

        UpdateGridSize size ->
            let
                simulationState =
                    model.simulationState
            in
            ( { model
                | simulationState = { simulationState | gridSize = size }
              }
            , Cmd.none
            )

        ShiftKeyDown pressed ->
            let
                simulationState =
                    model.simulationState
            in
            ( { model
                | simulationState = { simulationState | shiftPressed = pressed }
              }
            , Cmd.none
            )

        UpdateEnvironmentTimeOfDay timeOfDay ->
            let
                scene =
                    model.scene

                context =
                    scene.sceneContext

                environment =
                    context.environment
            in
            ( { model
                | scene =
                    { scene
                        | sceneContext =
                            { context
                                | environment = { environment | timeOfDay = timeOfDay }
                            }
                    }
              }
            , Cmd.none
            )

        UpdateEnvironmentWeather weather ->
            let
                scene =
                    model.scene

                context =
                    scene.sceneContext

                environment =
                    context.environment
            in
            ( { model
                | scene =
                    { scene
                        | sceneContext =
                            { context
                                | environment = { environment | weather = weather }
                            }
                    }
              }
            , Cmd.none
            )

        UpdateEnvironmentSeason season ->
            let
                scene =
                    model.scene

                context =
                    scene.sceneContext

                environment =
                    context.environment
            in
            ( { model
                | scene =
                    { scene
                        | sceneContext =
                            { context
                                | environment = { environment | season = season }
                            }
                    }
              }
            , Cmd.none
            )

        UpdateEnvironmentAtmosphere atmosphere ->
            let
                scene =
                    model.scene

                context =
                    scene.sceneContext

                environment =
                    context.environment
            in
            ( { model
                | scene =
                    { scene
                        | sceneContext =
                            { context
                                | environment = { environment | atmosphere = atmosphere }
                            }
                    }
              }
            , Cmd.none
            )

        UpdateSceneNarrative narrative ->
            let
                scene =
                    model.scene

                context =
                    scene.sceneContext
            in
            ( { model
                | scene =
                    { scene
                        | sceneContext = { context | narrative = narrative }
                    }
              }
            , Cmd.none
            )

        UpdateAmbientIntensity intensity ->
            let
                scene =
                    model.scene

                context =
                    scene.sceneContext

                lighting =
                    context.lighting
            in
            ( { model
                | scene =
                    { scene
                        | sceneContext =
                            { context
                                | lighting = { lighting | ambientIntensity = intensity }
                            }
                    }
              }
            , Cmd.none
            )

        UpdateAmbientColor color ->
            let
                scene =
                    model.scene

                context =
                    scene.sceneContext

                lighting =
                    context.lighting
            in
            ( { model
                | scene =
                    { scene
                        | sceneContext =
                            { context
                                | lighting = { lighting | ambientColor = color }
                            }
                    }
              }
            , Cmd.none
            )

        UpdateDirectionalIntensity intensity ->
            let
                scene =
                    model.scene

                context =
                    scene.sceneContext

                lighting =
                    context.lighting
            in
            ( { model
                | scene =
                    { scene
                        | sceneContext =
                            { context
                                | lighting = { lighting | directionalIntensity = intensity }
                            }
                    }
              }
            , Cmd.none
            )

        UpdateDirectionalColor color ->
            let
                scene =
                    model.scene

                context =
                    scene.sceneContext

                lighting =
                    context.lighting
            in
            ( { model
                | scene =
                    { scene
                        | sceneContext =
                            { context
                                | lighting = { lighting | directionalColor = color }
                            }
                    }
              }
            , Cmd.none
            )

        UpdateDirectionalAngle angle ->
            let
                scene =
                    model.scene

                context =
                    scene.sceneContext

                lighting =
                    context.lighting
            in
            ( { model
                | scene =
                    { scene
                        | sceneContext =
                            { context
                                | lighting = { lighting | directionalAngle = angle }
                            }
                    }
              }
            , Cmd.none
            )

        ToggleShadows ->
            let
                scene =
                    model.scene

                context =
                    scene.sceneContext

                lighting =
                    context.lighting
            in
            ( { model
                | scene =
                    { scene
                        | sceneContext =
                            { context
                                | lighting = { lighting | shadows = not lighting.shadows }
                            }
                    }
              }
            , Cmd.none
            )

        UpdateRenderQuality quality ->
            let
                scene =
                    model.scene

                context =
                    scene.sceneContext
            in
            ( { model
                | scene =
                    { scene
                        | sceneContext = { context | renderQuality = quality }
                    }
              }
            , Cmd.none
            )

        Undo ->
            case model.history of
                previousScene :: restHistory ->
                    ( { model
                        | scene = previousScene
                        , history = restHistory
                        , future = model.scene :: model.future
                      }
                    , sendSceneToThreeJs (sceneEncoder previousScene)
                    )

                [] ->
                    ( model, Cmd.none )

        Redo ->
            case model.future of
                nextScene :: restFuture ->
                    ( { model
                        | scene = nextScene
                        , history = model.scene :: model.history
                        , future = restFuture
                      }
                    , sendSceneToThreeJs (sceneEncoder nextScene)
                    )

                [] ->
                    ( model, Cmd.none )

        SaveScene ->
            ( model, saveSceneToStorage (sceneEncoder model.scene) )

        LoadScene ->
            ( model, loadSceneFromStorage () )

        SceneLoadedFromStorage sceneValue ->
            case Decode.decodeValue sceneDecoder sceneValue of
                Ok loadedScene ->
                    let
                        modelWithHistory =
                            saveToHistory model
                    in
                    ( { modelWithHistory
                        | scene = loadedScene
                        , initialScene = Just loadedScene
                      }
                    , sendSceneToThreeJs (sceneEncoder loadedScene)
                    )

                Err _ ->
                    ( model, Cmd.none )

        KeyDown key ->
            -- Ignore keyboard shortcuts when typing in an input field
            if model.simulationState.typingInInput then
                ( model, Cmd.none )
            else
                case key of
                    "Control" ->
                        ( { model | ctrlPressed = True }, Cmd.none )

                    " " ->
                        -- Space: toggle simulation
                        update (ToggleSimulation) model

                    "g" ->
                        -- G: translate mode
                        update (SetTransformMode Translate) model

                    "r" ->
                        -- R: rotate mode
                        update (SetTransformMode Rotate) model

                    "s" ->
                        -- S: scale mode
                        update (SetTransformMode Scale) model

                    "z" ->
                        -- Ctrl+Z: undo
                        if model.ctrlPressed then
                            update Undo model
                        else
                            ( model, Cmd.none )

                    "y" ->
                        -- Ctrl+Y: redo
                        if model.ctrlPressed then
                            update Redo model
                        else
                            ( model, Cmd.none )

                    "d" ->
                        -- D: duplicate selected
                        update DuplicateSelected model

                    "Delete" ->
                        -- Delete: delete selected
                        update DeleteSelected model

                    "Backspace" ->
                        -- Backspace: delete selected (alternative)
                        update DeleteSelected model

                    "Shift" ->
                        -- Shift: enable multi-select mode
                        update (ShiftKeyDown True) model

                    "Escape" ->
                        -- Escape: clear selection
                        update ClearSelection model

                    _ ->
                        ( model, Cmd.none )

        KeyUp key ->
            case key of
                "Control" ->
                    ( { model | ctrlPressed = False }, Cmd.none )

                "Shift" ->
                    -- Release multi-select mode
                    update (ShiftKeyDown False) model

                _ ->
                    ( model, Cmd.none )

        InputFocused ->
            let
                simState = model.simulationState
            in
            ( { model | simulationState = { simState | typingInInput = True } }, Cmd.none )

        InputBlurred ->
            let
                simState = model.simulationState
            in
            ( { model | simulationState = { simState | typingInInput = False } }, Cmd.none )

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

        VideoMsg videoMsg ->
            let
                ( updatedVideoModel, videoCmd ) =
                    Video.update videoMsg model.videoModel
            in
            ( { model | videoModel = updatedVideoModel }, Cmd.map VideoMsg videoCmd )

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
    { title = "Physics Simulator & Video Models"
    , body =
        [ div []
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

                Just Route.Gallery ->
                    VideoGallery.view model.galleryModel
                        |> Html.map GalleryMsg

                Just Route.SimulationGallery ->
                    SimulationGallery.view model.simulationGalleryModel
                        |> Html.map SimulationGalleryMsg

                Nothing ->
                    div [ class "app-container" ]
                        [ viewLeftPanel model
                        , viewCanvasContainer
                        , viewRightPanel model
                        , viewBottomBar model
                        ]
            ]
        ]
    }


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
            [ href "/simulations"
            , class (if model.route == Just Route.SimulationGallery then "active" else "")
            ]
            [ text "Simulation Gallery" ]
        , a
            [ href "/physics"
            , class (if model.route == Just Route.Physics then "active" else "")
            ]
            [ text "Physics Simulator" ]
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
        , div [ class "object-controls" ]
            [ button
                [ onClick DuplicateSelected
                , disabled (Set.isEmpty model.scene.selectedObjects && model.scene.selectedObject == Nothing)
                , title "Duplicate selected objects (D)"
                ]
                [ text "Duplicate (D)" ]
            , button
                [ onClick DeleteSelected
                , disabled (Set.isEmpty model.scene.selectedObjects && model.scene.selectedObject == Nothing)
                , title "Delete selected objects (Delete)"
                ]
                [ text "Delete" ]
            ]
        , div [ class "grid-controls" ]
            [ button
                [ onClick ToggleSnapToGrid
                , class (if model.simulationState.snapToGrid then "active" else "")
                , title "Toggle snap to grid"
                ]
                [ text (if model.simulationState.snapToGrid then "Grid: ON" else "Grid: OFF") ]
            , if model.simulationState.snapToGrid then
                div [ class "grid-size-control" ]
                    [ label [] [ text ("Grid: " ++ String.fromFloat model.simulationState.gridSize ++ "m") ]
                    , input
                        [ type_ "range"
                        , Html.Attributes.min "0.1"
                        , Html.Attributes.max "5.0"
                        , step "0.1"
                        , value (String.fromFloat model.simulationState.gridSize)
                        , onInput (\val -> UpdateGridSize (Maybe.withDefault 1.0 (String.toFloat val)))
                        ]
                        []
                    ]
              else
                text ""
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


viewSceneSettings : SceneContext -> Html Msg
viewSceneSettings context =
    div [ class "scene-settings" ]
        [ div [ class "setting-group" ]
            [ h4 [] [ text "Environment" ]
            , div [ class "control-row" ]
                [ label [] [ text "Time of Day:" ]
                , select [ value context.environment.timeOfDay, onInput UpdateEnvironmentTimeOfDay ]
                    [ option [ value "dawn" ] [ text "Dawn" ]
                    , option [ value "morning" ] [ text "Morning" ]
                    , option [ value "midday" ] [ text "Midday" ]
                    , option [ value "afternoon" ] [ text "Afternoon" ]
                    , option [ value "golden_hour" ] [ text "Golden Hour" ]
                    , option [ value "dusk" ] [ text "Dusk" ]
                    , option [ value "night" ] [ text "Night" ]
                    ]
                ]
            , div [ class "control-row" ]
                [ label [] [ text "Weather:" ]
                , select [ value context.environment.weather, onInput UpdateEnvironmentWeather ]
                    [ option [ value "clear" ] [ text "Clear" ]
                    , option [ value "cloudy" ] [ text "Cloudy" ]
                    , option [ value "overcast" ] [ text "Overcast" ]
                    , option [ value "rainy" ] [ text "Rainy" ]
                    , option [ value "stormy" ] [ text "Stormy" ]
                    , option [ value "foggy" ] [ text "Foggy" ]
                    , option [ value "snowy" ] [ text "Snowy" ]
                    ]
                ]
            , div [ class "control-row" ]
                [ label [] [ text "Season:" ]
                , select [ value context.environment.season, onInput UpdateEnvironmentSeason ]
                    [ option [ value "spring" ] [ text "Spring" ]
                    , option [ value "summer" ] [ text "Summer" ]
                    , option [ value "autumn" ] [ text "Autumn" ]
                    , option [ value "winter" ] [ text "Winter" ]
                    ]
                ]
            , div [ class "control-row" ]
                [ label [] [ text ("Atmosphere: " ++ String.fromFloat context.environment.atmosphere) ]
                , input
                    [ type_ "range"
                    , Html.Attributes.min "0"
                    , Html.Attributes.max "1"
                    , step "0.1"
                    , value (String.fromFloat context.environment.atmosphere)
                    , onInput (\val -> UpdateEnvironmentAtmosphere (Maybe.withDefault 0.5 (String.toFloat val)))
                    ]
                    []
                ]
            ]
        , div [ class "setting-group" ]
            [ h4 [] [ text "Scene Narrative" ]
            , textarea
                [ placeholder "Describe the overall scene, mood, and what's happening..."
                , value context.narrative
                , onInput UpdateSceneNarrative
                , onFocus InputFocused
                , onBlur InputBlurred
                , rows 3
                ]
                []
            ]
        , div [ class "setting-group" ]
            [ h4 [] [ text "Lighting" ]
            , div [ class "control-row" ]
                [ label [] [ text ("Ambient: " ++ String.fromFloat context.lighting.ambientIntensity) ]
                , input
                    [ type_ "range"
                    , Html.Attributes.min "0"
                    , Html.Attributes.max "1"
                    , step "0.1"
                    , value (String.fromFloat context.lighting.ambientIntensity)
                    , onInput (\val -> UpdateAmbientIntensity (Maybe.withDefault 0.4 (String.toFloat val)))
                    ]
                    []
                ]
            , div [ class "control-row" ]
                [ label [] [ text ("Directional: " ++ String.fromFloat context.lighting.directionalIntensity) ]
                , input
                    [ type_ "range"
                    , Html.Attributes.min "0"
                    , Html.Attributes.max "2"
                    , step "0.1"
                    , value (String.fromFloat context.lighting.directionalIntensity)
                    , onInput (\val -> UpdateDirectionalIntensity (Maybe.withDefault 0.8 (String.toFloat val)))
                    ]
                    []
                ]
            , div [ class "control-row" ]
                [ label [] [ text ("Angle: " ++ String.fromFloat context.lighting.directionalAngle ++ "°") ]
                , input
                    [ type_ "range"
                    , Html.Attributes.min "0"
                    , Html.Attributes.max "90"
                    , step "5"
                    , value (String.fromFloat context.lighting.directionalAngle)
                    , onInput (\val -> UpdateDirectionalAngle (Maybe.withDefault 45.0 (String.toFloat val)))
                    ]
                    []
                ]
            , div [ class "control-row" ]
                [ label [] [ text "Shadows:" ]
                , input
                    [ type_ "checkbox"
                    , checked context.lighting.shadows
                    , onClick ToggleShadows
                    ]
                    []
                ]
            ]
        , div [ class "setting-group" ]
            [ h4 [] [ text "Render Quality" ]
            , select [ value context.renderQuality, onInput UpdateRenderQuality ]
                [ option [ value "draft" ] [ text "Draft (Fast)" ]
                , option [ value "high" ] [ text "High (Balanced)" ]
                , option [ value "ultra" ] [ text "Ultra (Slow)" ]
                ]
            ]
        ]


viewLeftPanel : Model -> Html Msg
viewLeftPanel model =
    div [ class "left-panel" ]
        [ h2 [] [ text "Scene Settings" ]
        , viewSceneSettings model.scene.sceneContext
        , h2 [] [ text "Generation" ]
        , textarea
            [ placeholder "Describe a scene to generate..."
            , value model.uiState.textInput
            , onInput UpdateTextInput
            , onFocus InputFocused
            , onBlur InputBlurred
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
            , onFocus InputFocused
            , onBlur InputBlurred
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
        , h2 [] [ text "AI Populate Scene" ]
        , textarea
            [ placeholder "Add objects to scene (e.g., 'add 3 cars and 2 street lights in a parking lot')"
            , value model.uiState.populateInput
            , onInput UpdatePopulateInput
            , onFocus InputFocused
            , onBlur InputBlurred
            , disabled model.uiState.isPopulating
            ]
            []
        , div [ class "populate-controls" ]
            [ div [ class "control-group" ]
                [ label [] [ text ("Number of objects: " ++ String.fromInt model.uiState.populateNumObjects) ]
                , input
                    [ type_ "range"
                    , Html.Attributes.min "1"
                    , Html.Attributes.max "20"
                    , value (String.fromInt model.uiState.populateNumObjects)
                    , onInput (\val -> UpdatePopulateNumObjects (Maybe.withDefault 5 (String.toInt val)))
                    , disabled model.uiState.isPopulating
                    ]
                    []
                ]
            , div [ class "control-group" ]
                [ label [] [ text "Placement:" ]
                , select
                    [ value model.uiState.populatePlacementStrategy
                    , onInput UpdatePopulatePlacementStrategy
                    , disabled model.uiState.isPopulating
                    ]
                    [ option [ value "natural" ] [ text "Natural" ]
                    , option [ value "grid" ] [ text "Grid" ]
                    , option [ value "random" ] [ text "Random" ]
                    ]
                ]
            ]
        , button
            [ onClick PopulateScene
            , disabled (String.isEmpty (String.trim model.uiState.populateInput) || model.uiState.isPopulating)
            ]
            [ if model.uiState.isPopulating then
                span [ class "loading" ] []
              else
                text ""
            , text (if model.uiState.isPopulating then "Populating..." else "Populate")
            ]
        , h2 [] [ text "Motion & Animation" ]
        , textarea
            [ placeholder "Describe motion (e.g., 'car drives forward slowly', 'ball bounces 3 times')"
            , value model.uiState.motionInput
            , onInput UpdateMotionInput
            , onFocus InputFocused
            , onBlur InputBlurred
            , disabled model.uiState.isGeneratingMotion
            ]
            []
        , button
            [ onClick GenerateMotion
            , disabled (String.isEmpty (String.trim model.uiState.motionInput) || model.uiState.isGeneratingMotion || Dict.isEmpty model.scene.objects)
            ]
            [ if model.uiState.isGeneratingMotion then
                span [ class "loading" ] []
              else
                text ""
            , text (if model.uiState.isGeneratingMotion then "Generating..." else "Generate Motion")
            ]
        , case model.uiState.motionData of
            Just motionData ->
                div [ class "motion-result" ]
                    [ h4 [] [ text "Motion Generated" ]
                    , p [ class "motion-description" ] [ text motionData.description ]
                    ]

            Nothing ->
                text ""
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
                , onFocus InputFocused
                , onBlur InputBlurred
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
    in
    Sub.batch
        [ sendSelectionToElm SelectionChanged
        , sendTransformUpdateToElm TransformUpdated
        , sceneLoadedFromStorage SceneLoadedFromStorage
        , Browser.Events.onKeyDown (Decode.map KeyDown keyDecoder)
        , Browser.Events.onKeyUp (Decode.map KeyUp keyDecoder)
        , gallerySub
        , simulationGallerySub
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
    Decode.map4 Scene
        (Decode.field "objects" (Decode.dict physicsObjectDecoder))
        (Decode.maybe (Decode.field "selectedObject" Decode.string))
        (Decode.succeed Set.empty)
        (Decode.succeed defaultSceneContext)


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
    Http.post
        { url = "/api/generate"
        , body = Http.jsonBody (Encode.object [ ( "prompt", Encode.string prompt ) ])
        , expect = Http.expectJson SceneGeneratedResult sceneDecoder
        }


refineSceneRequest : Scene -> String -> Cmd Msg
refineSceneRequest scene prompt =
    Http.post
        { url = "/api/refine"
        , body = Http.jsonBody (Encode.object [ ( "scene", sceneEncoder scene ), ( "prompt", Encode.string prompt ) ])
        , expect = Http.expectJson SceneRefined sceneDecoder
        }


populateSceneRequest : Scene -> String -> Int -> String -> Cmd Msg
populateSceneRequest scene prompt numObjects placementStrategy =
    Http.post
        { url = "/api/scene/populate"
        , body =
            Http.jsonBody
                (Encode.object
                    [ ( "scene", sceneEncoder scene )
                    , ( "prompt", Encode.string prompt )
                    , ( "num_objects", Encode.int numObjects )
                    , ( "placement_strategy", Encode.string placementStrategy )
                    ]
                )
        , expect = Http.expectJson ScenePopulated sceneDecoder
        }


generateMotionRequest : Dict String PhysicsObject -> String -> Cmd Msg
generateMotionRequest objects motionPrompt =
    Http.post
        { url = "/api/motion/generate"
        , body =
            Http.jsonBody
                (Encode.object
                    [ ( "motion_prompt", Encode.string motionPrompt )
                    , ( "objects", Encode.dict identity physicsObjectEncoder objects )
                    , ( "duration", Encode.float 5.0 )
                    , ( "fps", Encode.int 60 )
                    ]
                )
        , expect = Http.expectJson MotionGenerated motionDataDecoder
        }


motionDataDecoder : Decode.Decoder MotionData
motionDataDecoder =
    Decode.map3 MotionData
        (Decode.field "animations" (Decode.dict Decode.value))
        (Decode.field "cameraAnimation" Decode.value)
        (Decode.field "description" Decode.string)


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