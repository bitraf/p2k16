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

  function register_account(payload) {
    var req = {};
    req.method = 'POST';
    req.url = '/service/register-account';
    req.data = payload;
    return $http(req);
  }

  function data_accounts() {
    var req = {};
    req.method = 'GET';
    req.url = '/data/account';
    return $http(req);
  }

  function data_account(account_id) {
    var req = {};
    req.method = 'GET';
    req.url = '/data/account';
    req.url += '/' + account_id;
    return $http(req);
  }

  function remove_membership(account_id, payload) {
    var req = {};
    req.method = 'POST';
    req.url = '/data/account';
    req.url += '/' + account_id;
    req.url += '/cmd/remove-membership';
    req.data = payload;
    return $http(req);
  }

  function create_membership(account_id, payload) {
    var req = {};
    req.method = 'POST';
    req.url = '/data/account';
    req.url += '/' + account_id;
    req.url += '/cmd/create-membership';
    req.data = payload;
    return $http(req);
  }

  function data_circles() {
    var req = {};
    req.method = 'GET';
    req.url = '/data/circle';
    return $http(req);
  }

  function data_companies() {
    var req = {};
    req.method = 'GET';
    req.url = '/data/company';
    return $http(req);
  }

  function data_company(company_id) {
    var req = {};
    req.method = 'GET';
    req.url = '/data/company';
    req.url += '/' + company_id;
    return $http(req);
  }

  function data_company_register(payload) {
    var req = {};
    req.method = 'POST';
    req.url = '/data/company';
    req.data = payload;
    return $http(req);
  }

  function data_company_update(company_id, payload) {
    var req = {};
    req.method = 'POST';
    req.url = '/data/company';
    req.url += '/' + company_id;
    req.data = payload;
    return $http(req);
  }


  /**
   * @lends CoreDataService.prototype
   */
  return {
    service_authz_login: service_authz_login,
    service_authz_logout: service_authz_logout,
    register_account: register_account,
    data_accounts: data_accounts,
    data_account: data_account,
    remove_membership: remove_membership,
    create_membership: create_membership,
    data_circles: data_circles,
    data_companies: data_companies,
    data_company: data_company,
    data_company_register: data_company_register,
    data_company_update: data_company_update
  };
};

var CoreDataServiceResolvers = {};
CoreDataServiceResolvers.data_accounts = function (CoreDataService) {
  return CoreDataService.data_accounts().then(function (res) { return res.data; });
};
CoreDataServiceResolvers.data_account = function (CoreDataService, $route) {
  var account_id = $route.current.params.account_id;
  return CoreDataService.data_account(account_id).then(function (res) { return res.data; });
};
CoreDataServiceResolvers.data_circles = function (CoreDataService) {
  return CoreDataService.data_circles().then(function (res) { return res.data; });
};
CoreDataServiceResolvers.data_companies = function (CoreDataService) {
  return CoreDataService.data_companies().then(function (res) { return res.data; });
};
CoreDataServiceResolvers.data_company = function (CoreDataService, $route) {
  var company_id = $route.current.params.company_id;
  return CoreDataService.data_company(company_id).then(function (res) { return res.data; });
};
