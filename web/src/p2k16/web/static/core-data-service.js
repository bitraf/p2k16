'use strict';
/**
 * @constructor
 */
function CoreDataService($http) {
  this.$http = $http;
  return this;
}

CoreDataService.prototype.service_authz_login = function (payload) {
    var req = {};
    req.method = 'POST';
    req.url = '/service/authz/log-in';
    req.data = payload;
    return this.$http(req);
};

CoreDataService.prototype.service_authz_logout = function (payload) {
    var req = {};
    req.method = 'POST';
    req.url = '/service/authz/log-out';
    req.data = payload;
    return this.$http(req);
};

CoreDataService.prototype.register_account = function (payload) {
    var req = {};
    req.method = 'POST';
    req.url = '/service/register-account';
    req.data = payload;
    return this.$http(req);
};

CoreDataService.prototype.data_account_list = function () {
    var req = {};
    req.method = 'GET';
    req.url = '/data/account';
    return this.$http(req);
};

CoreDataService.prototype.data_account = function (account_id) {
    var req = {};
    req.method = 'GET';
    req.url = '/data/account';
    req.url += '/' + account_id;
    return this.$http(req);
};

CoreDataService.prototype.remove_membership = function (account_id, payload) {
    var req = {};
    req.method = 'POST';
    req.url = '/data/account';
    req.url += '/' + account_id;
    req.url += '/cmd/remove-membership';
    req.data = payload;
    return this.$http(req);
};

CoreDataService.prototype.create_membership = function (account_id, payload) {
    var req = {};
    req.method = 'POST';
    req.url = '/data/account';
    req.url += '/' + account_id;
    req.url += '/cmd/create-membership';
    req.data = payload;
    return this.$http(req);
};

CoreDataService.prototype.set_stripe_token = function (account_id, payload) {
    var req = {};
    req.method = 'POST';
    req.url = '/data/account';
    req.url += '/' + account_id;
    req.url += '/cmd/set-stripe-token';
    req.data = payload;
    return this.$http(req);
};

CoreDataService.prototype.data_circle_list = function () {
    var req = {};
    req.method = 'GET';
    req.url = '/data/circle';
    return this.$http(req);
};

CoreDataService.prototype.data_company_list = function () {
    var req = {};
    req.method = 'GET';
    req.url = '/data/company';
    return this.$http(req);
};

CoreDataService.prototype.data_company = function (company_id) {
    var req = {};
    req.method = 'GET';
    req.url = '/data/company';
    req.url += '/' + company_id;
    return this.$http(req);
};

CoreDataService.prototype.data_company_add_employee = function (company_id, payload) {
    var req = {};
    req.method = 'POST';
    req.url = '/data/company';
    req.url += '/' + company_id;
    req.url += '/cmd/add-employee';
    req.data = payload;
    return this.$http(req);
};

CoreDataService.prototype.data_company_remove_employee = function (company_id, payload) {
    var req = {};
    req.method = 'POST';
    req.url = '/data/company';
    req.url += '/' + company_id;
    req.url += '/cmd/remove-employee';
    req.data = payload;
    return this.$http(req);
};

CoreDataService.prototype.data_company_add = function (payload) {
    var req = {};
    req.method = 'POST';
    req.url = '/data/company';
    req.data = payload;
    return this.$http(req);
};

CoreDataService.prototype.data_company_update = function (payload) {
    var req = {};
    req.method = 'PUT';
    req.url = '/data/company';
    req.data = payload;
    return this.$http(req);
};

var CoreDataServiceResolvers = {};
CoreDataServiceResolvers.data_account_list = function (CoreDataService) {
  return CoreDataService.data_account_list().then(function (res) { return res.data; });
};
CoreDataServiceResolvers.data_account = function (CoreDataService, $route) {
  var account_id = $route.current.params.account_id;
  return CoreDataService.data_account(account_id).then(function (res) { return res.data; });
};
CoreDataServiceResolvers.data_circle_list = function (CoreDataService) {
  return CoreDataService.data_circle_list().then(function (res) { return res.data; });
};
CoreDataServiceResolvers.data_company_list = function (CoreDataService) {
  return CoreDataService.data_company_list().then(function (res) { return res.data; });
};
CoreDataServiceResolvers.data_company = function (CoreDataService, $route) {
  var company_id = $route.current.params.company_id;
  return CoreDataService.data_company(company_id).then(function (res) { return res.data; });
};
