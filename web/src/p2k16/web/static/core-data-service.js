'use strict';

/**
 * @constructor
 */
function CoreDataService($http) {

    this.service_authz_login = function (payload) {
        var req = {};
        req.method = 'POST';
        req.url = '/service/authz/log-in';
        req.data = payload;
        return $http(req);
    };

    this.service_authz_logout = function (payload) {
        var req = {};
        req.method = 'POST';
        req.url = '/service/authz/log-out';
        req.data = payload;
        return $http(req);
    };

    this.register_account = function (payload) {
        var req = {};
        req.method = 'POST';
        req.url = '/service/register-account';
        req.data = payload;
        return $http(req);
    };

    this.data_account_list = function () {
        var req = {};
        req.method = 'GET';
        req.url = '/data/account';
        return $http(req);
    };

    this.data_account = function (account_id) {
        var req = {};
        req.method = 'GET';
        req.url = '/data/account';
        req.url += '/' + account_id;
        return $http(req);
    };

    this.data_account_summary = function (account_id) {
        var req = {};
        req.method = 'GET';
        req.url = '/data/account-summary';
        req.url += '/' + account_id;
        return $http(req);
    };

    this.remove_account_from_circle = function (payload) {
        var req = {};
        req.method = 'POST';
        req.url = '/data/account/remove-membership';
        req.data = payload;
        return $http(req);
    };

    this.add_account_to_circle = function (payload) {
        var req = {};
        req.method = 'POST';
        req.url = '/service/circle/create-membership';
        req.data = payload;
        return $http(req);
    };

    this.membership_set_stripe_token = function (payload) {
        var req = {};
        req.method = 'POST';
        req.url = '/membership/set-stripe-token';
        req.data = payload;
        return $http(req);
    };

    this.membership_details = function () {
        var req = {};
        req.method = 'GET';
        req.url = '/membership/details';
        return $http(req);
    };

    this.membership_set_membership = function (payload) {
        var req = {};
        req.method = 'POST';
        req.url = '/membership/set-membership';
        req.data = payload;
        return $http(req);
    };

    this.data_circle_list = function () {
        var req = {};
        req.method = 'GET';
        req.url = '/data/circle';
        return $http(req);
    };

    this.data_circle = function (circle_id) {
        var req = {};
        req.method = 'GET';
        req.url = '/data/circle';
        req.url += '/' + circle_id;
        return $http(req);
    };

    this.data_company_list = function () {
        var req = {};
        req.method = 'GET';
        req.url = '/data/company';
        return $http(req);
    };

    this.data_company = function (company_id) {
        var req = {};
        req.method = 'GET';
        req.url = '/data/company';
        req.url += '/' + company_id;
        return $http(req);
    };

    this.data_company_add_employee = function (company_id, payload) {
        var req = {};
        req.method = 'POST';
        req.url = '/data/company';
        req.url += '/' + company_id;
        req.url += '/cmd/add-employee';
        req.data = payload;
        return $http(req);
    };

    this.data_company_remove_employee = function (company_id, payload) {
        var req = {};
        req.method = 'POST';
        req.url = '/data/company';
        req.url += '/' + company_id;
        req.url += '/cmd/remove-employee';
        req.data = payload;
        return $http(req);
    };

    this.data_company_add = function (payload) {
        var req = {};
        req.method = 'POST';
        req.url = '/data/company';
        req.data = payload;
        return $http(req);
    };

    this.data_company_update = function (payload) {
        var req = {};
        req.method = 'PUT';
        req.url = '/data/company';
        req.data = payload;
        return $http(req);
    };

    this.service_start_reset_password = function (payload) {
        var req = {};
        req.method = 'POST';
        req.url = '/service/start-reset-password';
        req.data = payload;
        return $http(req);
    };
}

var CoreDataServiceResolvers = {};
CoreDataServiceResolvers.data_account_list = function (CoreDataService) {
  return CoreDataService.data_account_list().then(function (res) { return res.data; });
};
CoreDataServiceResolvers.data_account = function (CoreDataService, $route) {
  var account_id = $route.current.params.account_id;
  return CoreDataService.data_account(account_id).then(function (res) { return res.data; });
};
CoreDataServiceResolvers.data_account_summary = function (CoreDataService, $route) {
  var account_id = $route.current.params.account_id;
  return CoreDataService.data_account_summary(account_id).then(function (res) { return res.data; });
};
CoreDataServiceResolvers.membership_details = function (CoreDataService) {
  return CoreDataService.membership_details().then(function (res) { return res.data; });
};
CoreDataServiceResolvers.data_circle_list = function (CoreDataService) {
  return CoreDataService.data_circle_list().then(function (res) { return res.data; });
};
CoreDataServiceResolvers.data_circle = function (CoreDataService, $route) {
  var circle_id = $route.current.params.circle_id;
  return CoreDataService.data_circle(circle_id).then(function (res) { return res.data; });
};
CoreDataServiceResolvers.data_company_list = function (CoreDataService) {
  return CoreDataService.data_company_list().then(function (res) { return res.data; });
};
CoreDataServiceResolvers.data_company = function (CoreDataService, $route) {
  var company_id = $route.current.params.company_id;
  return CoreDataService.data_company(company_id).then(function (res) { return res.data; });
};
