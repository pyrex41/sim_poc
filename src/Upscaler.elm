module Upscaler exposing (Model, Msg(..), init, update, view)

import Html exposing (..)
import Html.Attributes exposing (..)
import Html.Events exposing (..)
import Http
import Json.Decode as Decode
import Json.Encode as Encode


-- MODEL


type alias Model =
    { imageUrl : String
    , scale : Int
    , prompt : String
    , dynamic : Int
    , sharpen : Int
    , collection : String
    , isUpscaling : Bool
    , result : Maybe UpscaleResult
    , error : Maybe String
    }


type alias UpscaleResult =
    { imageId : Int
    , status : String
    , message : String
    }


init : ( Model, Cmd Msg )
init =
    ( { imageUrl = ""
      , scale = 2
      , prompt = ""
      , dynamic = 6
      , sharpen = 0
      , collection = "upscaled"
      , isUpscaling = False
      , result = Nothing
      , error = Nothing
      }
    , Cmd.none
    )


-- UPDATE


type Msg
    = NoOp
    | UpdateImageUrl String
    | UpdateScale String
    | UpdatePrompt String
    | UpdateDynamic String
    | UpdateSharpen String
    | UpdateCollection String
    | UpscaleImage
    | UpscaleCompleted (Result Http.Error UpscaleResult)


update : Msg -> Model -> ( Model, Cmd Msg )
update msg model =
    case msg of
        NoOp ->
            ( model, Cmd.none )

        UpdateImageUrl url ->
            ( { model | imageUrl = url }, Cmd.none )

        UpdateScale scaleStr ->
            case String.toInt scaleStr of
                Just scale ->
                    ( { model | scale = scale }, Cmd.none )

                Nothing ->
                    ( model, Cmd.none )

        UpdatePrompt prompt ->
            ( { model | prompt = prompt }, Cmd.none )

        UpdateDynamic dynamicStr ->
            case String.toInt dynamicStr of
                Just dynamic ->
                    ( { model | dynamic = dynamic }, Cmd.none )

                Nothing ->
                    ( model, Cmd.none )

        UpdateSharpen sharpenStr ->
            case String.toInt sharpenStr of
                Just sharpen ->
                    ( { model | sharpen = sharpen }, Cmd.none )

                Nothing ->
                    ( model, Cmd.none )

        UpdateCollection collection ->
            ( { model | collection = collection }, Cmd.none )

        UpscaleImage ->
            if String.isEmpty model.imageUrl then
                ( { model | error = Just "Please enter an image URL" }, Cmd.none )

            else
                ( { model | isUpscaling = True, error = Nothing, result = Nothing }
                , upscaleImage model
                )

        UpscaleCompleted result ->
            case result of
                Ok upscaleResult ->
                    ( { model
                        | isUpscaling = False
                        , result = Just upscaleResult
                        , error = Nothing
                      }
                    , Cmd.none
                    )

                Err error ->
                    ( { model
                        | isUpscaling = False
                        , error = Just (httpErrorToString error)
                      }
                    , Cmd.none
                    )


-- HTTP


upscaleImage : Model -> Cmd Msg
upscaleImage model =
    let
        body =
            Encode.object
                [ ( "image_url", Encode.string model.imageUrl )
                , ( "scale", Encode.int model.scale )
                , ( "prompt", if String.isEmpty model.prompt then Encode.null else Encode.string model.prompt )
                , ( "dynamic", Encode.int model.dynamic )
                , ( "sharpen", Encode.int model.sharpen )
                , ( "collection", Encode.string model.collection )
                ]
    in
    Http.post
        { url = "/api/upscale-image"
        , body = Http.jsonBody body
        , expect = Http.expectJson UpscaleCompleted upscaleResultDecoder
        }


upscaleResultDecoder : Decode.Decoder UpscaleResult
upscaleResultDecoder =
    Decode.map3 UpscaleResult
        (Decode.field "image_id" Decode.int)
        (Decode.field "status" Decode.string)
        (Decode.field "message" Decode.string)


httpErrorToString : Http.Error -> String
httpErrorToString error =
    case error of
        Http.BadUrl url ->
            "Bad URL: " ++ url

        Http.Timeout ->
            "Request timeout"

        Http.NetworkError ->
            "Network error"

        Http.BadStatus status ->
            "Bad status: " ++ String.fromInt status

        Http.BadBody body ->
            "Bad body: " ++ body


-- VIEW


view : Model -> Html Msg
view model =
    div [ class "upscaler-container" ]
        [ div [ class "upscaler-header" ]
            [ h1 [] [ text "Image Upscaler" ]
            , p [ class "description" ]
                [ text "Upscale images using the Clarity Upscaler AI model from Replicate" ]
            ]
        , div [ class "upscaler-form" ]
            [ div [ class "form-group" ]
                [ label [] [ text "Image URL" ]
                , input
                    [ type_ "text"
                    , placeholder "https://example.com/image.jpg"
                    , value model.imageUrl
                    , onInput UpdateImageUrl
                    , class "form-control"
                    ]
                    []
                , small [ class "form-text" ]
                    [ text "Enter the URL of the image you want to upscale" ]
                ]
            , div [ class "form-row" ]
                [ div [ class "form-group" ]
                    [ label [] [ text ("Scale Factor: " ++ String.fromInt model.scale ++ "x") ]
                    , input
                        [ type_ "range"
                        , Html.Attributes.min "1"
                        , Html.Attributes.max "4"
                        , value (String.fromInt model.scale)
                        , onInput UpdateScale
                        , class "form-control"
                        ]
                        []
                    , small [ class "form-text" ] [ text "1x to 4x upscaling" ]
                    ]
                , div [ class "form-group" ]
                    [ label [] [ text ("HDR/Dynamic: " ++ String.fromInt model.dynamic) ]
                    , input
                        [ type_ "range"
                        , Html.Attributes.min "3"
                        , Html.Attributes.max "9"
                        , value (String.fromInt model.dynamic)
                        , onInput UpdateDynamic
                        , class "form-control"
                        ]
                        []
                    , small [ class "form-text" ] [ text "HDR level (3-9)" ]
                    ]
                , div [ class "form-group" ]
                    [ label [] [ text ("Sharpen: " ++ String.fromInt model.sharpen) ]
                    , input
                        [ type_ "range"
                        , Html.Attributes.min "0"
                        , Html.Attributes.max "10"
                        , value (String.fromInt model.sharpen)
                        , onInput UpdateSharpen
                        , class "form-control"
                        ]
                        []
                    , small [ class "form-text" ] [ text "Sharpening intensity (0-10)" ]
                    ]
                ]
            , div [ class "form-group" ]
                [ label [] [ text "Enhancement Prompt (Optional)" ]
                , textarea
                    [ placeholder "Leave empty to use default prompt"
                    , value model.prompt
                    , onInput UpdatePrompt
                    , class "form-control"
                    , rows 3
                    ]
                    []
                , small [ class "form-text" ]
                    [ text "Custom prompt for enhancement (optional, will use model default if empty)" ]
                ]
            , div [ class "form-group" ]
                [ label [] [ text "Collection" ]
                , input
                    [ type_ "text"
                    , placeholder "upscaled"
                    , value model.collection
                    , onInput UpdateCollection
                    , class "form-control"
                    ]
                    []
                ]
            , button
                [ onClick UpscaleImage
                , disabled model.isUpscaling
                , class "btn btn-primary"
                ]
                [ text (if model.isUpscaling then "Upscaling..." else "Upscale Image") ]
            ]
        , case model.error of
            Just errorMsg ->
                div [ class "alert alert-error" ]
                    [ text ("Error: " ++ errorMsg) ]

            Nothing ->
                text ""
        , case model.result of
            Just result ->
                div [ class "alert alert-success" ]
                    [ h3 [] [ text "Upscaling Started!" ]
                    , p [] [ text ("Image ID: " ++ String.fromInt result.imageId) ]
                    , p [] [ text ("Status: " ++ result.status) ]
                    , p [] [ text result.message ]
                    , a [ href "/image-gallery", class "btn btn-link" ]
                        [ text "View in Image Gallery" ]
                    ]

            Nothing ->
                text ""
        ]
