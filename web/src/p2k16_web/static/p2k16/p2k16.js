(function () {

    function config($routeProvider, $httpProvider) {
        $routeProvider.when("/public/unauthenticated", {
            controller: UnauthenticatedController,
            controllerAs: 'ctrl',
            templateUrl: 'static/unauthenticated.html'
        }).when("/", {
            controller: FrontPageController,
            controllerAs: 'ctrl',
            templateUrl: 'static/front-page.html'
        }).when("/tools", {
            controller: ToolsController,
            controllerAs: 'ctrl',
            templateUrl: 'static/tools.html'
        }).when("/membership", {
            controller: MembershipController,
            controllerAs: 'ctrl',
            templateUrl: 'static/membership.html'
        }).when("/doors", {
            controller: DoorsController,
            controllerAs: 'ctrl',
            templateUrl: 'static/doors.html'
        }).when("/admin", {
            controller: AdminController,
            controllerAs: 'ctrl',
            templateUrl: 'static/admin.html',
            resolve: {
                accounts: CoreDataServiceResolvers.data_accounts
            }
        }).when("/admin/:account_id", {
            controller: AdminAccountController,
            controllerAs: 'ctrl',
            templateUrl: 'static/admin-account.html',
            resolve: {
                account: CoreDataServiceResolvers.data_account,
                circles: CoreDataServiceResolvers.data_circles
            }
        }).otherwise("/");

        $httpProvider.interceptors.push('P2k16HttpInterceptor');
    }

    function run(P2k16, $location, $rootScope) {
        $rootScope.$on('$locationChangeStart', function () {
            var p = $location.path();

            if (p.startsWith("/public/")) {
                return;
            }

            if (P2k16.isLoggedIn()) {
                return;
            }

            // TODO: consider if we should show a login modal instead.
            $location.url("/public/unauthenticated");
        });

        $rootScope.p2k16 = P2k16;
    }

    /**
     * @constructor
     */
    function P2k16() {
        var self = this;
        self.errors = [];
        self.errors.dismiss = function (index) {
            self.errors.splice(index, 1);
        };

        self.account = null;

        function isLoggedIn() {
            return !!self.account;
        }

        function currentAccount() {
            return self.account;
        }

        function hasRole(circleName) {
            return self.account && _.some(self.account.circles, {"name": circleName});
        }

        function setLoggedIn(data) {
            self.account = data || null;
        }

        function addErrors(messages) {
            function add(m) {
                m = typeof(m) === "string" ? m : "";
                m = m.trim();
                if (m.length) {
                    self.errors.push(m);
                }
            }

            if (typeof messages === 'string') {
                add(messages);
            }
            else {
                angular.forEach(messages, add);
            }
        }

        if (window.p2k16.account) {
            setLoggedIn(window.p2k16.account);
            delete window["p2k16"];
        }

        /**
         * @lends P2k16.prototype
         */
        return {
            isLoggedIn: isLoggedIn,
            currentAccount: currentAccount,
            setLoggedIn: setLoggedIn,
            hasRole: hasRole,
            addErrors: addErrors,
            errors: self.errors
        }
    }

    /**
     * @param $http
     * @param {P2k16} P2k16
     * @param {CoreDataService} CoreDataService
     * @constructor
     */
    function AuthzService($http, P2k16, CoreDataService) {
        function logIn(form) {
            return $http.post('/service/authz/log-in', form).then(function (res) {
                P2k16.setLoggedIn(res.data);
            });
        }

        function logOut() {
            return CoreDataService.service_authz_logout().then(function () {
                P2k16.setLoggedIn(null);
            });
            // return $http.post('/service/authz/log-out', {}).then(function () {
            //     P2k16.setLoggedIn(null);
            // });
        }

        /**
         * @lends AuthzService.prototype
         */
        return {
            logIn: logIn,
            logOut: logOut
        }
    }

    function p2k16HeaderDirective() {
        function p2k16HeaderController($scope, $location, P2k16, AuthzService) {
            var self = this;
            self.currentAccount = P2k16.currentAccount;

            self.logout = function ($event) {
                $event.preventDefault();
                AuthzService.logOut().then(function () {
                    $location.url("/?random=" + Date.now());
                });
            };

            // self.showLoginModal = function ($event) {
            //     $event.preventDefault();
            //
            //     var instance = $uibModal.open({
            //         controller: LoginModalController,
            //         controllerAs: 'modal',
            //         templateUrl: 'modals/login.html'
            //     });
            // };
            //
            // function LoginModalController() {
            // }
        }

        return {
            restrict: 'E',
            scope: {active: '@', woot: '='},
            controller: p2k16HeaderController,
            controllerAs: 'header',
            templateUrl: "static/p2k16-header.html"
        }
    }

    function P2k16HttpInterceptor($rootScope, $q, P2k16) {
        return {
            responseError: function (rejection) {
                // console.log("responseError", "rejection", rejection);

                // window.x = rejection;
                // console.log('rejection.headers("content-type") === "application/vnd.json"', rejection.headers("content-type") === "application/vnd.error+json");
                if (rejection.headers("content-type") === "application/vnd.error+json" && rejection.data.message) {
                    // TODO: if rejection.status is in [400, 500), set level = warning, else danger.
                    P2k16.addErrors(rejection.data.message);
                    var deferred = $q.defer();
                    return deferred.promise;
                }

                return $q.reject(rejection);
            }
        }
    }

    function FrontPageController() {
        var self = this;
    }

    function ToolsController() {
        var self = this;
    }

    function MembershipController() {
        var self = this;

        self.doCheckout = function (token) {
            alert("Got Stripe token: " + token.id);
        };
    }

    function DoorsController($http) {
        var self = this;

        self.openDoor = function (door) {
            $http.post('/service/door/open', {door: door});
        }
    }

    function AdminController($http, accounts) {
        var self = this;

        self.accounts = accounts;
    }

    /**
     * @param $http
     * @param {CoreDataService} CoreDataService
     * @param account
     * @param circles
     * @constructor
     */
    function AdminAccountController($http, CoreDataService, account, circles) {
        var self = this;

        self.account = account;
        self.circles = circles;

        self.in_circle = function (circle) {
            return !!_.find(self.account.circles, {id: circle.id})
        };

        self.membership = function (circle, create) {
            var f = (create ? CoreDataService.create_membership : CoreDataService.remove_membership);
            f(self.account.id, {circle_id: circle.id}).then(function (account) {
                self.account = account.data;
            });
        }
    }

    /**
     * @param $http
     * @param $location
     * @param {AuthzService} AuthzService
     * @constructor
     */
    function UnauthenticatedController($location, $http, AuthzService) {
        var self = this;
        self.signupForm = {};
        self.loginForm = {
            'username': null,
            'password': null
        };

        self.registerAccount = function () {
            $http.post('/service/register-account', self.signupForm).then(function () {
            }).catch(angular.identity);
        };

        self.logIn = function () {
            AuthzService.logIn(self.loginForm).then(function () {
                $location.url("/");
            });
        };
    }

    angular.module('p2k16.app', ['ngRoute', 'ui.bootstrap', 'stripe.checkout'])
        .config(config)
        .run(run)
        .service("P2k16", P2k16)
        .service("CoreDataService", CoreDataService)
        .service("AuthzService", AuthzService)
        .service("P2k16HttpInterceptor", P2k16HttpInterceptor)
        .directive("p2k16Header", p2k16HeaderDirective);
})();
