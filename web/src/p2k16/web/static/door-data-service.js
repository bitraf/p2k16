'use strict';

/**
 * @constructor
 */
function DoorDataService($http) {

    this.recent_events = function () {
        var req = {};
        req.method = 'GET';
        req.url = '/service/door/recent-events';
        return $http(req);
    };

    this.open_door = function (payload) {
        var req = {};
        req.method = 'POST';
        req.url = '/service/door/open';
        req.data = payload;
        return $http(req);
    };

    this.door_service = function () {
        var req = {};
        req.method = 'GET';
        req.url = '/door-data-service.js';
        return $http(req);
    };
}

var DoorDataServiceResolvers = {};
DoorDataServiceResolvers.recent_events = function (DoorDataService) {
  return DoorDataService.recent_events().then(function (res) { return res.data; });
};
DoorDataServiceResolvers.door_service = function (DoorDataService) {
  return DoorDataService.door_service().then(function (res) { return res.data; });
};
