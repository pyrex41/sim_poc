module Auth exposing
    ( Auth
    , LoginState(..)
    , Msg(..)
    , init
    , update
    , view
    , isAuthenticated
    , checkAuth
    )

import Html exposing (..)
import Html.Attributes exposing (..)
import Html.Events exposing (..)
import Http
import Json.Decode as Decode
import Json.Encode as Encode


-- MODEL


type alias Auth =
    { username : String
    , password : String
    , loginState : LoginState
    , error : Maybe String
    }


type LoginState
    = Checking
    | NotLoggedIn
    | LoggingIn
    | LoggedIn


init : Auth
init =
    { username = ""
    , password = ""
    , loginState = Checking
    , error = Nothing
    }


-- UPDATE


type Msg
    = UpdateUsername String
    | UpdatePassword String
    | SubmitLogin
    | LoginResult (Result Http.Error LoginResponse)
    | CheckAuthResult (Result Http.Error ())
    | Logout


type alias LoginResponse =
    { message : String
    , username : String
    }


update : Msg -> Auth -> ( Auth, Cmd Msg )
update msg model =
    case msg of
        UpdateUsername username ->
            ( { model | username = username }, Cmd.none )

        UpdatePassword password ->
            ( { model | password = password }, Cmd.none )

        SubmitLogin ->
            ( { model | loginState = LoggingIn, error = Nothing }
            , login model.username model.password
            )

        LoginResult (Ok response) ->
            ( { model
                | loginState = LoggedIn
                , error = Nothing
                , password = ""
              }
            , Cmd.none
            )

        LoginResult (Err error) ->
            let
                errorMessage =
                    case error of
                        Http.BadUrl _ ->
                            "Invalid URL"

                        Http.Timeout ->
                            "Request timed out"

                        Http.NetworkError ->
                            "Network error"

                        Http.BadStatus status ->
                            if status == 401 then
                                "Invalid username or password"

                            else
                                "Server error: " ++ String.fromInt status

                        Http.BadBody body ->
                            "Invalid response: " ++ body
            in
            ( { model
                | loginState = NotLoggedIn
                , error = Just errorMessage
              }
            , Cmd.none
            )

        CheckAuthResult (Ok _) ->
            -- Already authenticated via cookie
            ( { model | loginState = LoggedIn }
            , Cmd.none
            )

        CheckAuthResult (Err _) ->
            -- Not authenticated, show login screen
            ( { model | loginState = NotLoggedIn }
            , Cmd.none
            )

        Logout ->
            ( { model
                | loginState = NotLoggedIn
                , username = ""
                , password = ""
                , error = Nothing
              }
            , logout
            )


-- COMMANDS


login : String -> String -> Cmd Msg
login username password =
    let
        body =
            Http.stringBody "application/x-www-form-urlencoded"
                ("username=" ++ username ++ "&password=" ++ password)

        decoder =
            Decode.map2 LoginResponse
                (Decode.field "message" Decode.string)
                (Decode.field "username" Decode.string)
    in
    Http.post
        { url = "/api/auth/login"
        , body = body
        , expect = Http.expectJson LoginResult decoder
        }


logout : Cmd Msg
logout =
    Http.post
        { url = "/api/auth/logout"
        , body = Http.emptyBody
        , expect = Http.expectWhatever (\_ -> Logout)
        }


checkAuth : Cmd Msg
checkAuth =
    -- Try to fetch videos (which requires auth) to check if authenticated
    -- If the cookie is valid, this will succeed; if not, it will fail with 401
    Http.get
        { url = "/api/videos?limit=1"
        , expect = Http.expectWhatever CheckAuthResult
        }


-- HELPERS


isAuthenticated : Auth -> Bool
isAuthenticated model =
    model.loginState == LoggedIn


-- VIEW


view : Auth -> Html Msg
view model =
    div
        [ class "login-container"
        , style "position" "fixed"
        , style "top" "0"
        , style "left" "0"
        , style "width" "100%"
        , style "height" "100%"
        , style "display" "flex"
        , style "align-items" "center"
        , style "justify-content" "center"
        , style "background" "linear-gradient(135deg, #667eea 0%, #764ba2 100%)"
        , style "z-index" "9999"
        ]
        [ div
            [ class "login-box"
            , style "background" "white"
            , style "padding" "2rem"
            , style "border-radius" "8px"
            , style "box-shadow" "0 10px 25px rgba(0,0,0,0.2)"
            , style "width" "100%"
            , style "max-width" "400px"
            ]
            [ h2
                [ style "margin-top" "0"
                , style "color" "#333"
                , style "text-align" "center"
                ]
                [ text "Best Video Project" ]
            , h3
                [ style "margin-top" "0"
                , style "color" "#666"
                , style "font-weight" "normal"
                , style "text-align" "center"
                ]
                [ text "Sign In" ]
            , case model.error of
                Just errorMsg ->
                    div
                        [ style "background" "#fee"
                        , style "color" "#c33"
                        , style "padding" "0.75rem"
                        , style "border-radius" "4px"
                        , style "margin-bottom" "1rem"
                        , style "border" "1px solid #fcc"
                        ]
                        [ text errorMsg ]

                Nothing ->
                    text ""
            , Html.form [ onSubmit SubmitLogin ]
                [ div [ style "margin-bottom" "1rem" ]
                    [ label
                        [ style "display" "block"
                        , style "margin-bottom" "0.5rem"
                        , style "color" "#555"
                        , style "font-weight" "500"
                        ]
                        [ text "Username" ]
                    , input
                        [ type_ "text"
                        , value model.username
                        , onInput UpdateUsername
                        , placeholder "Enter username"
                        , disabled (model.loginState == LoggingIn)
                        , style "width" "100%"
                        , style "padding" "0.75rem"
                        , style "border" "1px solid #ddd"
                        , style "border-radius" "4px"
                        , style "font-size" "1rem"
                        , style "box-sizing" "border-box"
                        ]
                        []
                    ]
                , div [ style "margin-bottom" "1.5rem" ]
                    [ label
                        [ style "display" "block"
                        , style "margin-bottom" "0.5rem"
                        , style "color" "#555"
                        , style "font-weight" "500"
                        ]
                        [ text "Password" ]
                    , input
                        [ type_ "password"
                        , value model.password
                        , onInput UpdatePassword
                        , placeholder "Enter password"
                        , disabled (model.loginState == LoggingIn)
                        , style "width" "100%"
                        , style "padding" "0.75rem"
                        , style "border" "1px solid #ddd"
                        , style "border-radius" "4px"
                        , style "font-size" "1rem"
                        , style "box-sizing" "border-box"
                        ]
                        []
                    ]
                , button
                    [ type_ "submit"
                    , disabled (model.loginState == LoggingIn || String.isEmpty model.username || String.isEmpty model.password)
                    , style "width" "100%"
                    , style "padding" "0.75rem"
                    , style "background" "#667eea"
                    , style "color" "white"
                    , style "border" "none"
                    , style "border-radius" "4px"
                    , style "font-size" "1rem"
                    , style "font-weight" "500"
                    , style "cursor" "pointer"
                    , style "transition" "background 0.2s"
                    ]
                    [ text
                        (if model.loginState == LoggingIn then
                            "Signing in..."

                         else
                            "Sign In"
                        )
                    ]
                ]
            , div
                [ style "margin-top" "1rem"
                , style "text-align" "center"
                , style "color" "#888"
                , style "font-size" "0.875rem"
                ]
                [ text "Team members: reuben, mike, harrison" ]
            ]
        ]
