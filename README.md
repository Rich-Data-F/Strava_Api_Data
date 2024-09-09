For exploration of the Strava version 3 API and what it enables to access.


https://developers.strava.com/docs/
https://developers.strava.com/docs/authentication/

Use of requests library preferred to swagger due to difficulty in installation of the latter

API set up with an existing account on Strava website https://www.strava.com/settings/api with developers.strava.com set as recall domain for the authorization

It may be fruitful to study 'behaviour' / functioning of the API on the Swagger playground (https://developers.strava.com/playground/#/Streams/getActivityStreams).

4. **Uploads** including categories of activity as sport_type: https://developers.strava.com/docs/uploads/ Activity_type is deprecated

*DEFINITION*

_GET https://www.strava.com/api/v3/uploads/:id <br>
Example Request_

_    $ curl -G https://www.strava.com/api/v3/uploads/123456 \
        -H "Authorization: Bearer 83ebeabdec09f6670863766f792ead24d61fe3f9" _ 

*Example Response* 

_    {
      "id": 123456,
      "id_str": "123456",
      "external_id": "98765.gpx",
      "error": null,
      "status": "Your activity is ready.",
      "activity_id": 153243126_