'use strict';

/**
 * @constructor
 */
function BadgeDataService($http) {

    this.badge_descriptions = function () {
        var req = {};
        req.method = 'GET';
        req.url = '/badge/badge-descriptions';
        return $http(req);
    };

    this.create = function (payload) {
        var req = {};
        req.method = 'POST';
        req.url = '/badge/create-badge';
        req.data = payload;
        return $http(req);
    };

    this.recent_badges = function () {
        var req = {};
        req.method = 'GET';
        req.url = '/badge/recent-badges';
        return $http(req);
    };

    this.badges_for_user = function (account_id) {
        var req = {};
        req.method = 'GET';
        req.url = '/badge/badges-for-user';
        req.url += '/' + account_id;
        return $http(req);
    };
}

var BadgeDataServiceResolvers = {};
BadgeDataServiceResolvers.badge_descriptions = function (BadgeDataService) {
  return BadgeDataService.badge_descriptions().then(function (res) { return res.data; });
};
BadgeDataServiceResolvers.recent_badges = function (BadgeDataService) {
  return BadgeDataService.recent_badges().then(function (res) { return res.data; });
};
BadgeDataServiceResolvers.badges_for_user = function (BadgeDataService, $route) {
  var account_id = $route.current.params.account_id;
  return BadgeDataService.badges_for_user(account_id).then(function (res) { return res.data; });
};
