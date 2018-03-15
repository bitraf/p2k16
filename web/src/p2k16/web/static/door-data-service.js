'use strict';
/**
 * @constructor
 */
function DoorDataService($http) {
  this.$http = $http;
  return this;
}

DoorDataService.prototype.recent_events = function () {
    var req = {};
    req.method = 'GET';
    req.url = '/service/door/recent-events';
    return this.$http(req);
};

DoorDataService.prototype.open_door = function (payload) {
    var req = {};
    req.method = 'POST';
    req.url = '/service/door/open';
    req.data = payload;
    return this.$http(req);
};

DoorDataService.prototype.door_service = function () {
    var req = {};
    req.method = 'GET';
    req.url = '/door-data-service.js';
    return this.$http(req);
};

var DoorDataServiceResolvers = {};
DoorDataServiceResolvers.recent_events = function (DoorDataService) {
  return DoorDataService.recent_events().then(function (res) { return res.data; });
};
DoorDataServiceResolvers.door_service = function (DoorDataService) {
  return DoorDataService.door_service().then(function (res) { return res.data; });
};
