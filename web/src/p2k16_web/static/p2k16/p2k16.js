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
        $rootScope.$on('$locationChangeStart', function () {
            var p = $location.path();

            if (p.startsWith("/public/")) {
                return;
            }

            if (P2k16.isLoggedIn()) {
                return;
            }

            $location.url("/public/register-user");
        });

        $rootScope.p2k16 = P2k16;
    }

    function P2k16() {
        var self = this;
        self.errors = [];
        self.errors.dismiss = function (index) {
            self.errors.splice(index, 1);
        };

        var user = window.p2k16.user;
        delete window["p2k16"];

        function isLoggedIn() {
            return !!user;
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
                console.log("responseError", "rejection", rejection);

                window.x = rejection;
                console.log('rejection.headers("content-type") === "application/vnd.json"', rejection.headers("content-type") === "application/vnd.error+json");
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

    angular.module('p2k16.app', ['ngRoute'])
        .config(config)
        .run(run)
        .controller(FrontPageController)
        .service("P2k16", P2k16)
        .service("P2k16HttpInterceptor", P2k16HttpInterceptor);
})();
