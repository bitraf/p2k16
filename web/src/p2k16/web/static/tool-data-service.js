'use strict';

/**
 * @constructor
 */
function ToolDataService($http) {

    this.recent_events = function () {
        var req = {};
        req.method = 'GET';
        req.url = '/service/tool/recent-events';
        return $http(req);
    };

    this.checkout_tool = function (payload) {
        var req = {};
        req.method = 'POST';
        req.url = '/service/tool/checkout';
        req.data = payload;
        return $http(req);
    };

    this.checkin_tool = function (payload) {
        var req = {};
        req.method = 'POST';
        req.url = '/service/tool/checkin';
        req.data = payload;
        return $http(req);
    };

    this.data_tool_list = function () {
        var req = {};
        req.method = 'GET';
        req.url = '/data/tool';
        return $http(req);
    };

    this.data_tool = function (tool_id) {
        var req = {};
        req.method = 'GET';
        req.url = '/data/tool';
        req.url += '/' + tool_id;
        return $http(req);
    };

    this.data_tool_update = function (payload) {
        var req = {};
        req.method = 'PUT';
        req.url = '/data/tool';
        req.data = payload;
        return $http(req);
    };

    this.data_tool_add = function (payload) {
        var req = {};
        req.method = 'POST';
        req.url = '/data/tool';
        req.data = payload;
        return $http(req);
    };

    this.add_tool_circle_requirement = function (tool_id, circle_id, payload) {
        var req = {};
        req.method = 'POST';
        req.url = '/data/tool';
        req.url += '/' + tool_id;
        req.url += '/circle-requirements';
        req.url += '/' + circle_id;
        req.data = payload;
        return $http(req);
    };

    this.remove_tool_circle_requirement = function (tool_id, circle_id, payload) {
        var req = {};
        req.method = 'DELETE';
        req.url = '/data/tool';
        req.url += '/' + tool_id;
        req.url += '/circle-requirements';
        req.url += '/' + circle_id;
        req.data = payload;
        return $http(req);
    };

    this.tool_service = function () {
        var req = {};
        req.method = 'GET';
        req.url = '/tool-data-service.js';
        return $http(req);
    };
}

var ToolDataServiceResolvers = {};
ToolDataServiceResolvers.recent_events = function (ToolDataService) {
  return ToolDataService.recent_events().then(function (res) { return res.data; });
};
ToolDataServiceResolvers.data_tool_list = function (ToolDataService) {
  return ToolDataService.data_tool_list().then(function (res) { return res.data; });
};
ToolDataServiceResolvers.data_tool = function (ToolDataService, $route) {
  var tool_id = $route.current.params.tool_id;
  return ToolDataService.data_tool(tool_id).then(function (res) { return res.data; });
};
ToolDataServiceResolvers.tool_service = function (ToolDataService) {
  return ToolDataService.tool_service().then(function (res) { return res.data; });
};
