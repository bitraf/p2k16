'use strict';
/**
 * @constructor
 */
function DoorDataService($http) {
  this.$http = $http;
  return this;
}

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
DoorDataServiceResolvers.door_service = function (CoreDataService) {
  return CoreDataService.door_service().then(function (res) { return res.data; });
};
