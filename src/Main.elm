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
import Url exposing (Url)
import Video
import VideoDetail
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
    , videoDetailModel : Maybe VideoDetail.Model
    , galleryModel : VideoGallery.Model
    , simulationGalleryModel : SimulationGallery.Model
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
                newRoute =
                    Route.fromUrl url

                ( videoDetailModel, videoDetailCmd ) =
                    case newRoute of
                        Just (Route.VideoDetail videoId) ->
                            let
                                ( detailModel, detailCmd ) =
                                    VideoDetail.init videoId
                            in
                            ( Just detailModel, Cmd.map VideoDetailMsg detailCmd )

                        _ ->
                            ( Nothing, Cmd.none )

                -- Refresh gallery when navigating to it
                galleryCmd =
                    case newRoute of
                        Just Route.Gallery ->
                            Task.perform (always (GalleryMsg VideoGallery.FetchVideos)) (Task.succeed ())

                        _ ->
                            Cmd.none
            in
            ( { model | url = url, route = newRoute, videoDetailModel = videoDetailModel }
            , Cmd.batch [ videoDetailCmd, galleryCmd ]
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

                _ ->
                    ( model, Cmd.none )

        KeyUp key ->
            case key of
                "Control" ->
                    ( { model | ctrlPressed = False }, Cmd.none )

                _ ->
                    ( model, Cmd.none )

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

                Just (Route.VideoDetail _) ->
                    case model.videoDetailModel of
                        Just videoDetailModel ->
                            VideoDetail.view videoDetailModel
                                |> Html.map VideoDetailMsg

                        Nothing ->
                            div [ class "loading" ] [ text "Loading..." ]

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