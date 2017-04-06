(function () {

    var membershipType = [
        {
            value: 500,
            name: 'Vanlig'
        },
        {
            value: 300,
            name: 'Støttemedlem'
        },
        {
            value: 1500,
            name: 'Filantrop'
        }
    ];

    function config($routeProvider) {
        $routeProvider.when("/", {
            controller: FrontPageController,
            controllerAs: 'ctrl',
            templateUrl: 'static/front-page.html'
        }).otherwise("/")
    }

    function run() {

    }

    function FrontPageController($http) {
        var self = this;

        self.user = window.user;

        self.openDoor = function () {
            $http.post('/door/open');
        }
    }

    var deps = ['ngRoute'];
    angular.module('p2k16.app', deps)
        .config(config)
        .run(run)
        .controller(FrontPageController);
})();
