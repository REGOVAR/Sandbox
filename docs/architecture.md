https://coggle.it/diagram/Vv7ygtaFfxlmVQIE

## Server
### Technology
* REST API
 * To interact between server and client(s)
 * Standard, simple
* aioHTTP
 * To expose webservice via a REST API
 * Simple, flexible, realtime with websockets
* Marshmallow
 * To serialise and deserialise formats
* Database: PostgeSQL + SQLAlchemy Python
 * To store and to query
 * Get the VAT/Gemini code?

### Format
All formats are available for upload and download
* Input: FastQ / bcl / bed...
* Intermediate: BAM / CRAM / VCF / gVCF
* Ouput: xls / ods / png + pdf report

## Client
No logic, user interface only
###Native
* Technology: Qt
* Dashboard
* Job queued monitoring
* Internationalization (French and English)

###Web
* DNS
* Wiki
 * Technology: Gollum
* community.regovar.org
 * Forum
 * Plugins (download and upload) 

## EasterEggs
