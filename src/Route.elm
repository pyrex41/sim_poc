module Route exposing (Route(..), fromUrl, toHref)

import Url exposing (Url)
import Url.Parser as Parser exposing (Parser, oneOf, s, int, (</>))


type Route
    = Physics
    | Videos
    | VideoDetail Int
    | Gallery
    | SimulationGallery
    | Images
    | ImageDetail Int
    | ImageGallery


parser : Parser (Route -> a) a
parser =
    oneOf
        [ Parser.map Videos Parser.top
        , Parser.map Physics (s "physics")
        , Parser.map Videos (s "videos")
        , Parser.map VideoDetail (s "video" </> int)
        , Parser.map Gallery (s "gallery")
        , Parser.map SimulationGallery (s "simulations")
        , Parser.map Images (s "images")
        , Parser.map ImageDetail (s "image" </> int)
        , Parser.map ImageGallery (s "image-gallery")
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

        VideoDetail id ->
            "/video/" ++ String.fromInt id

        Gallery ->
            "/gallery"

        SimulationGallery ->
            "/simulations"

        Images ->
            "/images"

        ImageDetail id ->
            "/image/" ++ String.fromInt id

        ImageGallery ->
            "/image-gallery"
