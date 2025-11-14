module Route exposing (Route(..), fromUrl, toHref)

import Url exposing (Url)
import Url.Parser as Parser exposing (Parser, oneOf, s)


type Route
    = Physics
    | Videos
    | Gallery
    | SimulationGallery


parser : Parser (Route -> a) a
parser =
    oneOf
        [ Parser.map Videos Parser.top
        , Parser.map Physics (s "physics")
        , Parser.map Videos (s "videos")
        , Parser.map Gallery (s "gallery")
        , Parser.map SimulationGallery (s "simulations")
        ]


fromUrl : Url -> Maybe Route
fromUrl url =
    Parser.parse parser url


toHref : Route -> String
toHref route =
    case route of
        Physics ->
            "/physics"

        Videos ->
            "/videos"

        Gallery ->
            "/gallery"

        SimulationGallery ->
            "/simulations"
