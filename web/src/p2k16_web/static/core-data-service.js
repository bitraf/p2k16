'use strict';
/**
 * @constructor
 */
var CoreDataService = function ($http) {
  function service_authz_login(payload) {
    var req = {};
    req.method = 'POST';
    req.url = '/service/authz/log-in';
    req.data = payload;
    return $http(req);
  }

  function service_authz_logout(payload) {
    var req = {};
    req.method = 'POST';
    req.url = '/service/authz/log-out';
    req.data = payload;
    return $http(req);
  }

  function register_user(payload) {
    var req = {};
    req.method = 'POST';
    req.url = '/service/register-user';
    req.data = payload;
    return $http(req);
  }

  function data_user() {
    var req = {};
    req.method = 'GET';
    req.url = '/data/user';
    return $http(req);
  }

  /**
   * @lends CoreDataService.prototype
   */
  return {
    service_authz_login: service_authz_login,
    service_authz_logout: service_authz_logout,
    register_user: register_user,
    data_user: data_user
  }
};

CoreDataService.resolve = {};
CoreDataService.resolve.service_authz_login = function(CoreDataService) {
  return CoreDataService.service_authz_login().then(function (res) { return res.data; });
};
CoreDataService.resolve.service_authz_logout = function(CoreDataService) {
  return CoreDataService.service_authz_logout().then(function (res) { return res.data; });
};
CoreDataService.resolve.register_user = function(CoreDataService) {
  return CoreDataService.register_user().then(function (res) { return res.data; });
};
CoreDataService.resolve.data_user = function(CoreDataService) {
  return CoreDataService.data_user().then(function (res) { return res.data; });
};
