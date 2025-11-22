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
    | Audio
    | AudioDetail Int
    | AudioGallery
    | VideoToText
    | VideoToTextGallery
    | Auth
    | BriefGallery
    | CreativeBriefEditor
    | AIVideoGallery


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
        , Parser.map Audio (s "audio")
        , Parser.map AudioDetail (s "audio" </> int)
        , Parser.map AudioGallery (s "audio-gallery")
        , Parser.map VideoToText (s "video-to-text")
        , Parser.map VideoToTextGallery (s "video-to-text-gallery")
        , Parser.map Auth (s "auth")
        , Parser.map BriefGallery (s "briefs")
        , Parser.map CreativeBriefEditor (s "creative")
        , Parser.map AIVideoGallery (s "ai-videos")
        ]


fromUrl : Url -> Maybe Route
fromUrl url =
    case Parser.parse parser url of
        Just route ->
            Just route

        Nothing ->
            Just Videos  -- Default to videos


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

        Audio ->
            "/audio"

        AudioDetail id ->
            "/audio/" ++ String.fromInt id

        AudioGallery ->
            "/audio-gallery"

        VideoToText ->
            "/video-to-text"

        VideoToTextGallery ->
            "/video-to-text-gallery"

        Auth ->
            "/auth"

        BriefGallery ->
            "/briefs"

        CreativeBriefEditor ->
            "/creative"

        AIVideoGallery ->
            "/ai-videos"
