(function () {

    function config($routeProvider, $httpProvider) {
        $routeProvider.when("/public/unauthenticated", {
            controller: UnauthenticatedController,
            controllerAs: 'ctrl',
            templateUrl: p2k16_resources.unauthenticated_html
        }).when("/", {
            controller: FrontPageController,
            controllerAs: 'ctrl',
            templateUrl: p2k16_resources.front_page_html
        }).when("/membership", {
            controller: MembershipController,
            controllerAs: 'ctrl',
            templateUrl: p2k16_resources.membership_html,
            resolve: {
                membership_details: CoreDataServiceResolvers.membership_details
            }
        }).when("/admin", {
            controller: AdminController,
            controllerAs: 'ctrl',
            templateUrl: p2k16_resources.admin_html
        }).when("/admin/account", {
            controller: AdminAccountListController,
            controllerAs: 'ctrl',
            templateUrl: p2k16_resources.admin_account_list_html,
            resolve: {
                accounts: CoreDataServiceResolvers.data_account_list
            }
        }).when("/admin/account/:account_id", {
            controller: AdminAccountDetailController,
            controllerAs: 'ctrl',
            templateUrl: p2k16_resources.admin_account_detail_html,
            resolve: {
                account: CoreDataServiceResolvers.data_account,
                circles: CoreDataServiceResolvers.data_circle_list
            }
        }).when("/admin/company", {
            controller: AdminCompanyListController,
            controllerAs: 'ctrl',
            templateUrl: p2k16_resources.admin_company_list_html,
            resolve: {
                companies: CoreDataServiceResolvers.data_company_list
            }
        }).when("/admin/company/new", {
            controller: AdminCompanyDetailController,
            controllerAs: 'ctrl',
            templateUrl: p2k16_resources.admin_company_detail_html,
            resolve: {
                accounts: CoreDataServiceResolvers.data_account_list,
                company: _.constant({active: true})
            }
        }).when("/admin/company/:company_id", {
            controller: AdminCompanyDetailController,
            controllerAs: 'ctrl',
            templateUrl: p2k16_resources.admin_company_detail_html,
            resolve: {
                accounts: CoreDataServiceResolvers.data_account_list,
                company: CoreDataServiceResolvers.data_company
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
    function P2k16Message(text, cssClass) {
        this.text = text;
        this.cssClass = cssClass;
    }

    /**
     * @constructor
     */
    function P2k16() {
        var self = this;
        self.messages = [];
        self.messages.dismiss = function (index) {
            self.messages.splice(index, 1);
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

        function addInfos(messages) {
            return addMessages(messages, "alert-info");
        }

        function addErrors(messages) {
            return addMessages(messages, "alert-danger");
        }

        function addMessages(messages, cssClass) {
            function add(text, cssClass) {
                text = typeof(text) === "string" ? text : "";
                text = text.trim();
                if (text.length) {
                    self.messages.push(new P2k16Message(text, cssClass));
                }
            }

            if (typeof messages === 'string') {
                add(messages, cssClass);
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
            addInfos: addInfos,
            messages: self.messages
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

            $scope.isNavCollapsed = true;
            $scope.isCollapsed = false;
            $scope.isCollapsedHorizontal = false;
        }

        return {
            restrict: 'E',
            scope: {active: '@', woot: '='},
            controller: p2k16HeaderController,
            controllerAs: 'header',
            templateUrl: p2k16_resources.p2k16_header_html
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

    /**
     * @param {DoorDataService} DoorDataService
     * @param {P2k16} P2k16
     */
    function FrontPageController(DoorDataService, P2k16) {
        var self = this;

        self.openDoors = function (doors) {
            DoorDataService.open_door({doors: doors}).then(function (res) {
                var msg = res.message || "The door is open";
                P2k16.addInfos(msg);
            });
        }
    }

    function getMembershipTypes() {
        // TODO: Move this to model
        return [
            {plan: 'medlem1500', name: 'Filantropmedlemskap (1500 kr)', price: 1500},
            {plan: 'medlem500', name: 'Vanlig medlemskap (500 kr)', price: 500},
            {plan: 'medlem300', name: 'Støttemedlemskap (300 kr)', price: 300},
            {plan: 'none', name: 'Inaktiv (0 kr)', price: 0}
        ];
    }

    function MembershipController($uibModal, $log, CoreDataService, membership_details) {
        var self = this;

        self.membership_details = membership_details;

        var spinner = new Spinner().spin();

        function startSpinner() {
            // Stripe takes a long time. Need a spinner
            document.body.appendChild(spinner.el)
        }

        function stopSpinner() {
            document.body.removeChild(spinner.el)
        }

        function updateDetails() {
            startSpinner();
            CoreDataService.membership_details().then(function (res) {
                self.membership_details = res.data;
                stopSpinner();
            });
        }

        self.doCheckout = function (token) {
            startSpinner();
            CoreDataService.membership_set_stripe_token(token).then(function () {
                // Update membership_details from api
                updateDetails();
            });
        };

        self.items = getMembershipTypes();

        self.openChangeMembership = function () {
            var modalInstance = $uibModal.open({
                animation: true,
                ariaLabelledBy: 'modal-title',
                ariaDescribedBy: 'modal-body',
                templateUrl: 'updateMembershipTemplate.html',
                controller: ChangeMembershipController,
                controllerAs: 'ctrl',
                resolve: {
                    items: function () {
                        return self.items;
                    },
                    membership_details: self.membership_details
                }
            });

            modalInstance.result.then(function (selectedItem) {
                startSpinner();
                CoreDataService.membership_set_membership(selectedItem).then(function () {
                    updateDetails();
                });

            }, function () {
                $log.info('Modal dismissed at: ' + new Date());
            });
        };
    }

    function ChangeMembershipController($scope, $uibModalInstance, membership_details) {
        var self = this;

        $scope.items = getMembershipTypes();

        $scope.selectedItem = $scope.items[0];
        for (var i = 0; i < $scope.items.length; ++i)
            if ($scope.items[i].price == membership_details.fee) {
                $scope.selectedItem = $scope.items[i];
                break;
            }

        self.ok = function () {
            $uibModalInstance.close($scope.selectedItem);
        };

        self.cancel = function () {
            $uibModalInstance.dismiss('cancel');
        };
    }

    /**
     * @param $http
     * @param $location
     * @param {CoreDataService} CoreDataService
     * @constructor
     */
    function AdminController($http, $location, CoreDataService) {
        var self = this;
    }

    /**
     * @param {CoreDataService} CoreDataService
     * @param accounts
     * @constructor
     */
    function AdminAccountListController(CoreDataService, accounts) {
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
    function AdminAccountDetailController($http, CoreDataService, account, circles) {
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
     * @param {CoreDataService} CoreDataService
     * @param companies
     * @constructor
     */
    function AdminCompanyListController(CoreDataService, companies) {
        var self = this;

        self.companies = companies;
    }

    /**
     * @param $location
     * @param accounts
     * @param company
     * @param {CoreDataService} CoreDataService
     * @constructor
     */
    function AdminCompanyDetailController($location, accounts, company, CoreDataService) {
        var self = this;
        var isNew;

        self.accounts = accounts;

        function setCompany(company) {
            self.company = angular.copy(company);
            isNew = !self.company.id;
            self.title = isNew ? "New company" : self.company.name;
        }

        setCompany(company);

        self.save = function () {
            var q = self.company.id ? CoreDataService.data_company_update(self.company) : CoreDataService.data_company_add(self.company);

            q.then(function (res) {
                if (isNew) {
                    $location.url("/admin/company/" + res.data.id);
                } else {
                    setCompany(res.data);
                    self.form.$setPristine();
                }
            });
        };

        self.existingEmployeeFilter = function (account) {
            return _.findIndex(self.company.employees, {account: {username: account.username}}) === -1
        };

        self.removeEmployee = function ($event, a) {
            $event.preventDefault();
            CoreDataService.data_company_remove_employee(company.id, {account_id: a.id})
                .then(function (res) {
                    setCompany(res.data);
                });
        };

        self.addEmployee = function ($event, a) {
            $event.preventDefault();
            self.query = '';
            CoreDataService.data_company_add_employee(company.id, {account_id: a.id})
                .then(function (res) {
                    setCompany(res.data);
                });
        };
    }

    /**
     * @param $location
     * @param {P2k16} P2k16
     * @param {CoreDataService} CoreDataService
     * @param {AuthzService} AuthzService
     * @constructor
     */
    function UnauthenticatedController($location, P2k16, CoreDataService, AuthzService) {
        var self = this;
        self.signupForm = {};
        self.loginForm = {
            'username': null,
            'password': null
        };

        self.registerAccount = function () {
            CoreDataService.register_account(self.signupForm).then(function (res) {
                self.signupForm = {};
                P2k16.addInfos("Account created, please log in.");
            });
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
        .service("DoorDataService", DoorDataService)
        .service("AuthzService", AuthzService)
        .service("P2k16HttpInterceptor", P2k16HttpInterceptor)
        .directive("p2k16Header", p2k16HeaderDirective);
})();
