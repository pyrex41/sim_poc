module ImageDetail exposing (Model, Msg, init, update, view, subscriptions)

import Html exposing (..)
import Html.Attributes exposing (..)
import Http
import Json.Decode as Decode
import Time


-- MODEL


type alias Model =
    { imageId : Int
    , image : Maybe ImageRecord
    , error : Maybe String
    , isPolling : Bool
    }


type alias ImageRecord =
    { id : Int
    , prompt : String
    , imageUrl : String
    , modelId : String
    , createdAt : String
    , status : String
    , metadata : Maybe Decode.Value
    }


init : Int -> ( Model, Cmd Msg )
init imageId =
    ( { imageId = imageId
      , image = Nothing
      , error = Nothing
      , isPolling = True
      }
    , fetchImage imageId
    )



-- UPDATE


type Msg
    = ImageFetched (Result Http.Error ImageRecord)
    | PollTick Time.Posix


update : Msg -> Model -> ( Model, Cmd Msg )
update msg model =
    case msg of
        ImageFetched result ->
            case result of
                Ok image ->
                    let
                        -- Stop polling if image is completed or failed
                        shouldStopPolling =
                            image.status == "completed" || image.status == "failed" || image.status == "canceled"
                    in
                    ( { model
                        | image = Just image
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
                ( model, fetchImage model.imageId )

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
    div [ class "image-detail-page" ]
        [ h1 [] [ text "Image Generation Status" ]
        , case model.error of
            Just err ->
                div [ class "error" ] [ text err ]

            Nothing ->
                text ""
        , case model.image of
            Just image ->
                viewImageDetail image

            Nothing ->
                div [ class "loading" ] [ text "Loading image information..." ]
        ]


viewImageDetail : ImageRecord -> Html Msg
viewImageDetail image =
    div [ class "image-detail" ]
        [ div [ class "image-info" ]
            [ h2 [] [ text "Image Details" ]
            , div [ class "info-row" ]
                [ span [ class "label" ] [ text "Status: " ]
                , span [ class ("status status-" ++ String.toLower image.status) ]
                    [ text (statusText image.status) ]
                ]
            , div [ class "info-row" ]
                [ span [ class "label" ] [ text "Model: " ]
                , span [] [ text image.modelId ]
                ]
            , div [ class "info-row" ]
                [ span [ class "label" ] [ text "Prompt: " ]
                , p [ class "prompt" ] [ text image.prompt ]
                ]
            , div [ class "info-row" ]
                [ span [ class "label" ] [ text "Created: " ]
                , span [] [ text image.createdAt ]
                ]
            ]
        , case image.status of
            "completed" ->
                if String.isEmpty image.imageUrl then
                    div [ class "error" ] [ text "Image completed but no URL available" ]

                else
                    div [ class "image-viewer" ]
                        [ h3 [] [ text "Generated Image" ]
                        , img
                            [ src image.imageUrl
                            , attribute "width" "100%"
                            , attribute "style" "max-width: 800px; border-radius: 8px;"
                            ]
                            []
                        , div [ class "image-actions" ]
                            [ a
                                [ href image.imageUrl
                                , download ""
                                , class "download-button"
                                ]
                                [ text "Download Image" ]
                            ]
                        ]

            "processing" ->
                div [ class "processing" ]
                    [ div [ class "spinner" ] []
                    , p [] [ text "Your image is being generated... This may take 30-60 seconds." ]
                    ]

            "failed" ->
                div [ class "error" ]
                    [ text (case extractErrorMessage image of
                        Just errorMsg ->
                            "Image generation failed: " ++ errorMsg

                        Nothing ->
                            "Image generation failed. Please try again with different parameters."
                    ) ]

            "canceled" ->
                div [ class "info" ]
                    [ text "Image generation was canceled." ]

            _ ->
                div [ class "info" ]
                    [ text ("Status: " ++ image.status) ]
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


extractErrorMessage : ImageRecord -> Maybe String
extractErrorMessage imageRecord =
    -- Try to extract error message from metadata
    case imageRecord.metadata of
        Just metadataValue ->
            Decode.decodeValue (Decode.field "error" Decode.string) metadataValue
                |> Result.toMaybe

        Nothing ->
            Nothing



-- HTTP


fetchImage : Int -> Cmd Msg
fetchImage imageId =
    Http.get
        { url = "/api/images/" ++ String.fromInt imageId
        , expect = Http.expectJson ImageFetched imageDecoder
        }


imageDecoder : Decode.Decoder ImageRecord
imageDecoder =
    Decode.map7 ImageRecord
        (Decode.field "id" Decode.int)
        (Decode.field "prompt" Decode.string)
        (Decode.field "image_url" Decode.string)
        (Decode.field "model_id" Decode.string)
        (Decode.field "created_at" Decode.string)
        (Decode.field "status" Decode.string)
        (Decode.maybe (Decode.field "metadata" Decode.value))


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
