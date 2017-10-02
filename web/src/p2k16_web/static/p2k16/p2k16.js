(function () {

    function config($routeProvider, $httpProvider) {
        $routeProvider.when("/", {
            controller: FrontPageController,
            controllerAs: 'ctrl',
            templateUrl: 'static/front-page.html'
        }).when("/public/register-user", {
            controller: RegisterUserController,
            controllerAs: 'ctrl',
            templateUrl: 'static/register-user.html'
        }).otherwise("/");

        $httpProvider.interceptors.push('P2k16HttpInterceptor');
    }

    function run(P2k16, $location, $rootScope) {
        $rootScope.$on('$locationChangeStart', function (event) {
            // console.log("$locationChangeStart!", event);
            var p = $location.path();
            // console.log("$location.path()", p);

            if (p.startsWith("/public/")) {
                return;
            }

            if (P2k16.isLoggedIn()) {
                return;
            }

            $location.url("/public/register-user");
        });
    }

    function P2k16() {
        var self = this;
        self.errors = [];

        var user = window.p2k16.user;
        delete window["p2k16"];

        function isLoggedIn() {
            return !!user;
        }

        function addErrors(messages) {
            console.log("p2k16", "messages", messages);
            if (typeof messages === 'string') {
                self.errors.push(messages);
            }
            else {
                angular.forEach(messages, function (message) {
                    self.errors.push(message);
                });
            }

            console.log("self.errors", self.errors);
        }

        return {
            isLoggedIn: isLoggedIn,
            addErrors: addErrors,
            errors: self.errors
        }
    }

    function P2k16HttpInterceptor($rootScope, $q, P2k16) {
        console.log("P2k16HttpInterceptor", arguments);
        return {
            responseError: function (rejection) {
                // console.log("responseError", "rejection", rejection);

                if (rejection.status === 400 && rejection.data.messages) {
                    P2k16.addErrors(rejection.data.messages);
                    var deferred = $q.defer();
                    return deferred.promise;
                }

                return $q.reject(rejection);
            }
        }
    }

    function FrontPageController($http) {
        var self = this;

        self.user = window.user;

        self.openDoor = function () {
            $http.post('/door/open');
        }
    }

    function RegisterUserController($http) {
        var self = this;
        self.form = {};
        self.form.username = "asd";

        self.registerUser = function () {
            $http.post('/service/register-user', self.form).then(function () {
                console.log("response", arguments);
            }).catch(angular.identity);
        }
    }

    var deps = ['ngRoute'];
    angular.module('p2k16.app', deps)
        .config(config)
        .run(run)
        .controller(FrontPageController)
        .service("P2k16", P2k16)
        .service("P2k16HttpInterceptor", P2k16HttpInterceptor);
})();
