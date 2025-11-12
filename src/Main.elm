port module Main exposing (main)

import Browser
import Dict exposing (Dict)
import Html exposing (..)
import Html.Attributes exposing (..)
import Html.Events exposing (..)
import Http
import Json.Decode as Decode
import Json.Encode as Encode


-- MAIN


main : Program () Model Msg
main =
    Browser.element
        { init = init
        , update = update
        , view = view
        , subscriptions = subscriptions
        }


-- MODEL


type alias Model =
    { scene : Scene
    , uiState : UiState
    , simulationState : SimulationState
    , initialScene : Maybe Scene
    }


type alias Scene =
    { objects : Dict String PhysicsObject
    , selectedObject : Maybe String
    }


type alias UiState =
    { textInput : String
    , isGenerating : Bool
    , errorMessage : Maybe String
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


init : () -> ( Model, Cmd Msg )
init _ =
    ( { scene =
            { objects = Dict.empty
            , selectedObject = Nothing
            }
      , uiState =
            { textInput = ""
            , isGenerating = False
            , errorMessage = Nothing
            }
      , simulationState =
            { isRunning = False
            , transformMode = Translate
            }
      , initialScene = Nothing
      }
    , Cmd.none
    )


-- UPDATE


type Msg
    = NoOp
    | UpdateTextInput String
    | GenerateScene
    | SceneGenerated Encode.Value
    | SceneGeneratedResult (Result Http.Error Scene)
    | ObjectClicked String
    | UpdateObjectTransform String Transform
    | UpdateObjectProperty String String Float
    | ToggleSimulation
    | ResetSimulation
    | SetTransformMode TransformMode
    | ClearError
    | SelectionChanged (Maybe String)
    | TransformUpdated { objectId : String, transform : Transform }


update : Msg -> Model -> ( Model, Cmd Msg )
update msg model =
    case msg of
        NoOp ->
            ( model, Cmd.none )

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
             in
             let
                 updatedScene =
                     { scene
                         | objects = Dict.map (\_ obj -> updateObject obj) scene.objects
                     }
             in
            ( { model | scene = updatedScene }
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
                    in
                    ( { model
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


-- VIEW


view : Model -> Html Msg
view model =
    div [ class "app-container" ]
        [ viewLeftPanel model
        , viewCanvasContainer
        , viewRightPanel model
        , viewBottomBar model
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
            [ text (if model.uiState.isGenerating then "Generating..." else "Generate Scene") ]
        , case model.uiState.errorMessage of
            Just error ->
                div [ class "error" ]
                    [ text error
                    , button [ onClick ClearError ] [ text "×" ]
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
    Sub.batch
        [ sendSelectionToElm SelectionChanged
        , sendTransformUpdateToElm TransformUpdated
        ]


-- PORTS


port sendSceneToThreeJs : Encode.Value -> Cmd msg


port sendSelectionToThreeJs : String -> Cmd msg


port sendSimulationCommand : String -> Cmd msg


port sendSelectionToElm : (Maybe String -> msg) -> Sub msg


port sendTransformModeToThreeJs : String -> Cmd msg


port sendTransformUpdateToElm : ({ objectId : String, transform : Transform } -> msg) -> Sub msg


-- DECODERS


sceneDecoder : Decode.Decoder Scene
sceneDecoder =
    Decode.map2 Scene
        (Decode.field "objects" (Decode.dict physicsObjectDecoder))
        (Decode.maybe (Decode.field "selectedObject" Decode.string))


physicsObjectDecoder : Decode.Decoder PhysicsObject
physicsObjectDecoder =
    Decode.map4 PhysicsObject
        (Decode.field "id" Decode.string)
        (Decode.field "transform" transformDecoder)
        (Decode.field "physicsProperties" physicsPropertiesDecoder)
        (Decode.field "visualProperties" visualPropertiesDecoder)


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
        { url = "http://127.0.0.1:8000/api/generate"
        , body = Http.jsonBody (Encode.object [ ( "prompt", Encode.string prompt ) ])
        , expect = Http.expectJson SceneGeneratedResult sceneDecoder
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
    Encode.object
        [ ( "id", Encode.string obj.id )
        , ( "transform", transformEncoder obj.transform )
        , ( "physicsProperties", physicsPropertiesEncoder obj.physicsProperties )
        , ( "visualProperties", visualPropertiesEncoder obj.visualProperties )
        ]


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