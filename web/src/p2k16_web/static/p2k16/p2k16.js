(function () {

    function config($routeProvider, $httpProvider) {
        $routeProvider.when("/", {
            controller: FrontPageController,
            controllerAs: 'ctrl',
            templateUrl: 'static/front-page.html'
        }).when("/tools", {
            controller: ToolsController,
            controllerAs: 'ctrl',
            templateUrl: 'static/tools.html'
        }).when("/doors", {
            controller: DoorsController,
            controllerAs: 'ctrl',
            templateUrl: 'static/doors.html'
        }).when("/public/unauthenticated", {
            controller: UnauthenticatedController,
            controllerAs: 'ctrl',
            templateUrl: 'static/unauthenticated.html'
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

        self.user = null;

        function isLoggedIn() {
            return !!self.user;
        }

        function currentUser() {
            return self.user;
        }

        function setLoggedIn(data) {
            self.user = data || null;
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

        if (window.p2k16.user) {
            setLoggedIn(window.p2k16.user);
            delete window["p2k16"];
        }

        return {
            isLoggedIn: isLoggedIn,
            currentUser: currentUser,
            setLoggedIn: setLoggedIn,
            addErrors: addErrors,
            errors: self.errors
        }
    }

    /**
     * @constructor
     */
    function AuthzService(P2k16, $http) {
        function logIn(form) {
            return $http.post('/service/authz/log-in', form).then(function (res) {
                P2k16.setLoggedIn(res.data);
            });
        }

        function logOut() {
            return $http.post('/service/authz/log-out', {}).then(function () {
                P2k16.setLoggedIn(null);
            });
        }

        return {
            logIn: logIn,
            logOut: logOut
        }
    }

    function p2k16HeaderDirective() {
        function p2k16HeaderController($scope, $location, P2k16, AuthzService) {
            var self = this;
            self.currentUser = P2k16.currentUser;

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

    function DoorsController($http) {
        var self = this;

        self.openDoor = function (door) {
            $http.post('/service/door/open', {door: door});
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

        self.registerUser = function () {
            $http.post('/service/register-user', self.signupForm).then(function () {
            }).catch(angular.identity);
        };

        self.logIn = function () {
            AuthzService.logIn(self.loginForm).then(function () {
                $location.url("/");
            });
        };
    }

    angular.module('p2k16.app', ['ngRoute', 'ui.bootstrap'])
        .config(config)
        .run(run)
        .controller(FrontPageController)
        .service("P2k16", P2k16)
        .service("AuthzService", AuthzService)
        .service("P2k16HttpInterceptor", P2k16HttpInterceptor)
        .directive("p2k16Header", p2k16HeaderDirective);
})();
