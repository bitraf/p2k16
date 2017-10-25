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

  function data_users() {
    var req = {};
    req.method = 'GET';
    req.url = '/data/user';
    return $http(req);
  }

  function data_user(user_id) {
    var req = {};
    req.method = 'GET';
    req.url = '/data/user';
    req.url += '/' + user_id;
    return $http(req);
  }


  /**
   * @lends CoreDataService.prototype
   */
  return {
    service_authz_login: service_authz_login,
    service_authz_logout: service_authz_logout,
    register_user: register_user,
    data_users: data_users,
    data_user: data_user
  };
};

var CoreDataServiceResolvers = {};
CoreDataServiceResolvers.data_users = function (CoreDataService) {
  return CoreDataService.data_users().then(function (res) { return res.data; });
};
CoreDataServiceResolvers.data_user = function (CoreDataService, $route) {
  var user_id = $route.current.params.user_id;
  return CoreDataService.data_user(user_id).then(function (res) { return res.data; });
};
