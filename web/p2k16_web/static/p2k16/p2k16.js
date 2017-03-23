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

    function FrontPageController() {
        var self = this;

        self.user = window.user;
    }

    var deps = ['ngRoute'];
    angular.module('p2k16.app', deps)
        .config(config)
        .run(run)
        .controller(FrontPageController);
})();
