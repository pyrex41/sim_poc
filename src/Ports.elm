port module Ports exposing (..)

import Json.Encode as E


-- Note: File cannot be sent directly through ports. Use E.Value instead
-- port fileSelected : File -> Cmd msg

-- Request JavaScript to read a file and convert to base64
port requestFileRead : () -> Cmd msg

-- Receive base64 encoded file data from JavaScript
port fileLoaded : (String -> msg) -> Sub msg

port navigateTo : String -> Cmd msg

port setApiKey : String -> Cmd msg