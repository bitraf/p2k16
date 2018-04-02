(function () {

    function config($routeProvider, $httpProvider) {
        $routeProvider.when("/public/unauthenticated", {
            controller: UnauthenticatedController,
            controllerAs: 'ctrl',
            templateUrl: p2k16_resources.unauthenticated_html
        }).when("/", {
            controller: FrontPageController,
            controllerAs: 'ctrl',
            templateUrl: p2k16_resources.front_page_html,
            resolve: {
                recent_events: DoorDataServiceResolvers.recent_events
            }
        }).when("/membership", {
            controller: MembershipController,
            controllerAs: 'ctrl',
            templateUrl: p2k16_resources.membership_html,
            resolve: {
                membership_details: CoreDataServiceResolvers.membership_details
            }
        }).when("/my-profile", {
            controller: MyProfileController,
            controllerAs: 'ctrl',
            templateUrl: p2k16_resources.my_profile_html,
            resolve: {
                badgeDescriptions: BadgeDataServiceResolvers.badge_descriptions
            }
        });

        // Badge
        $routeProvider.when("/badges", {
            controller: BadgesFrontPageController,
            controllerAs: 'ctrl',
            templateUrl: p2k16_resources.badges_front_page_html,
            resolve: {
                recentBadges: BadgeDataServiceResolvers.recent_badges,
                badgeDescriptions: BadgeDataServiceResolvers.badge_descriptions
            }
        });

        // User
        $routeProvider.when("/user/:account_id", {
            controller: UserDetailController,
            controllerAs: 'ctrl',
            templateUrl: p2k16_resources.user_detail_html,
            resolve: {
                summary: CoreDataServiceResolvers.data_account_summary,
                badgeDescriptions: BadgeDataServiceResolvers.badge_descriptions
            }
        });

        // Admin
        $routeProvider.when("/admin", {
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
        }).when("/admin/circle", {
            controller: AdminCircleListController,
            controllerAs: 'ctrl',
            templateUrl: p2k16_resources.admin_circle_list_html,
            resolve: {
                circles: CoreDataServiceResolvers.data_circle_list
            }
        }).when("/admin/circle/:circle_id", {
            controller: AdminCircleDetailController,
            controllerAs: 'ctrl',
            templateUrl: p2k16_resources.admin_circle_detail_html,
            resolve: {
                circle: CoreDataServiceResolvers.data_circle
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
    function Listeners($rootScope, key) {
        var self = this;
        self.args = [];

        var eventName = "Listeners-" + key;

        function add($scope, listener) {
            var destructor = $rootScope.$on(eventName, function () {
                console.log("listener args", self.args);
                listener.apply(null, self.args);
            });
            $scope.$on("$destroy", destructor);
        }

        function notify() {
            console.log("args", self.args);

            self.args = arguments;
            $rootScope.$emit(eventName);
            self.args = [];
        }

        /**
         * @lends Listeners.prototype
         */
        return {
            add: add,
            notify: notify
        };
    }

    /**
     * @constructor
     */
    function P2k16($rootScope) {
        var self = this;
        self.$rootScope = $rootScope;
        self.messages = [];
        self.messages.dismiss = function (index) {
            self.messages.splice(index, 1);
        };

        self.account = null;

        /**
         * @type {Listeners}
         */
        self.accountListeners = new Listeners($rootScope, "account");

        function isLoggedIn() {
            return !!self.account;
        }

        function currentAccount() {
            return self.account;
        }

        function refreshAccount(updated) {
            console.log("refreshing account");
            _.merge(self.account, updated);
            self.accountListeners.notify(self.account);
        }

        function refreshAccountFromResponse(res) {
            return refreshAccount(res.data);
        }

        function isInCircle(circleName) {
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

        function canAdminCircle(circleId) {
            return !!_.find(self.circlesWithAdminAccess, {id: circleId});
        }

        if (window.p2k16.account) {
            setLoggedIn(window.p2k16.account);
        }

        self.circlesWithAdminAccess = window.p2k16.circlesWithAdminAccess || [];

        window.p2k16 = undefined;

        /**
         * @lends P2k16.prototype
         */
        return {
            isLoggedIn: isLoggedIn,
            currentAccount: currentAccount,
            refreshAccount: refreshAccount,
            refreshAccountFromResponse: refreshAccountFromResponse,
            accountListeners: self.accountListeners,
            setLoggedIn: setLoggedIn,
            hasRole: isInCircle,
            addErrors: addErrors,
            addInfos: addInfos,
            messages: self.messages,

            canAdminCircle: canAdminCircle,
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
     * @param recent_events
     */
    function FrontPageController(DoorDataService, P2k16, recent_events) {
        var self = this;

        self.openDoors = function (doors) {
            DoorDataService.open_door({doors: doors}).then(function (res) {
                var msg = res.message || "The door is open";
                P2k16.addInfos(msg);
            });
        };

        self.recent_events = recent_events;
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
     * @param $scope
     * @param {P2k16} P2k16
     * @param badgeDescriptions
     * @constructor
     */
    function MyProfileController($scope, P2k16, badgeDescriptions) {
        var self = this;

        P2k16.accountListeners.add($scope, function (newValue) {
            console.log("updated", newValue);
            updateBadges(newValue);
        });

        function updateBadges(account) {
            self.badges = _.values(account.badges);
        }

        self.badges = [];
        self.newBadge = {};
        self.descriptions = badgeDescriptions;

        updateBadges(P2k16.currentAccount());
    }

    /*************************************************************************
     * Badges
     */

    /**
     * @param {CoreDataService} CoreDataService
     * @param {BadgeDataService} BadgeDataService
     * @param {P2k16} P2k16
     * @param badgeDescriptions
     * @param recentBadges
     */
    function BadgesFrontPageController(CoreDataService, BadgeDataService, P2k16, badgeDescriptions, recentBadges) {
        var self = this;

        self.badgeDescriptions = badgeDescriptions;
        self.recentBadges = recentBadges;

        self.createBadge = function () {
            BadgeDataService.create(self.newBadge).then(P2k16.refreshAccountFromResponse);
        };
    }

    /*************************************************************************
     * User
     */

    /**
     * @param {CoreDataService} CoreDataService
     * @param {BadgeDataService} BadgeDataService
     * @param {P2k16} P2k16
     * @param summary
     * @param badgeDescriptions
     */
    function UserDetailController(CoreDataService, BadgeDataService, P2k16, summary, badgeDescriptions) {
        var self = this;

        self.account = summary.account;
        self.badges = summary.badges;
        self.summary = summary;
        self.badgeDescriptions = badgeDescriptions;
    }


    /*************************************************************************
     * Admin
     */

    /**
     * @constructor
     */
    function AdminController() {
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
            var form = {
                accountId: self.account.id,
                circleId: circle.id
            };

            var f = create ? CoreDataService.add_account_to_circle : CoreDataService.remove_account_from_circle;
            f(form).then(function (account) {
                self.account = account.data;
            });
        }
    }

    /**
     * @param companies
     * @constructor
     */
    function AdminCompanyListController(companies) {
        var self = this;

        self.companies = companies;
    }

    /**
     * @param {CoreDataService} CoreDataService
     * @param circles
     * @constructor
     */
    function AdminCircleListController(CoreDataService, circles) {
        var self = this;

        self.circles = circles;
    }

    /**
     * @param {CoreDataService} CoreDataService
     * @param circle
     * @constructor
     */
    function AdminCircleDetailController(CoreDataService, circle) {
        var self = this;

        self.addMemberForm = {};

        function update(data) {
            self.circle = data;

            if (!self.members) {
                self.members = [];
            }

            if (data._embedded) {
                var embedded = data._embedded;
                delete data._embedded;
                self.members.length = 0;
                Array.prototype.unshift.apply(self.members, embedded.members);
                self.adminCircle = embedded.adminCircle;
            }
        }

        update(circle);

        self.removeMember = function (accountId) {
            var form = {
                accountId: accountId,
                circleId: self.circle.id
            };
            CoreDataService.remove_account_from_circle(form).then(function (res) {
                update(res.data);
            });
        };
        self.addMember = function () {
            var form = {
                accountUsername: self.addMemberForm.username,
                circleId: self.circle.id
            };
            self.addMemberForm = {};
            CoreDataService.add_account_to_circle(form).then(function (res) {
                update(res.data);
            });
        };
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

        self.removeEmployee = function ($event, employee) {
            $event.preventDefault();
            CoreDataService.data_company_remove_employee(company.id, {accountId: employee.account_id})
                .then(function (res) {
                    setCompany(res.data);
                });
        };

        self.addEmployee = function ($event, account) {
            $event.preventDefault();
            self.query = '';
            CoreDataService.data_company_add_employee(company.id, {accountId: account.id})
                .then(function (res) {
                    setCompany(res.data);
                });
        };
    }

    /**
     * @param $location
     * @param $uibModal
     * @param {P2k16} P2k16
     * @param {CoreDataService} CoreDataService
     * @param {AuthzService} AuthzService
     * @constructor
     */
    function UnauthenticatedController($location, $uibModal, P2k16, CoreDataService, AuthzService) {
        var self = this;
        self.signupForm = {};
        self.loginForm = {
            'username': null,
            'password': null
        };

        self.registerAccount = function () {
            CoreDataService.register_account(self.signupForm).then(function () {
                self.signupForm = {};
                P2k16.addInfos("Account created, please log in.");
            });
        };

        self.logIn = function () {
            AuthzService.logIn(self.loginForm).then(function () {
                $location.url("/");
            });
        };

        self.resetPassword = function () {
            var username = self.loginForm.username;
            console.log('username', username);
            var modalInstance = $uibModal.open({
                animation: true,
                templateUrl: 'unauthenticated/reset-password-modal.html',
                controller: function ($uibModalInstance) {
                    var self = this;
                    console.log('username', username);
                    self.username = username;
                    self.ok = function () {
                        CoreDataService.service_start_reset_password({username: self.username}).then(function (res) {
                            console.log("res", res.data);
                            self.message = res.data.message;
                        });
                    };
                    self.dismiss = function () {
                        $uibModalInstance.dismiss('dismissed');
                    };
                    self.cancel = function () {
                        $uibModalInstance.dismiss('cancel');
                    };
                },
                controllerAs: 'ctrl'
            });

            modalInstance.result.then(function (values) {
            }, angular.identity);
        }
    }

    angular.module('p2k16.app', ['ngRoute', 'ui.bootstrap', 'stripe.checkout'])
        .config(config)
        .run(run)
        .service("P2k16", P2k16)
        .service("BadgeDataService", BadgeDataService)
        .service("CoreDataService", CoreDataService)
        .service("DoorDataService", DoorDataService)
        .service("AuthzService", AuthzService)
        .service("P2k16HttpInterceptor", P2k16HttpInterceptor)
        .directive("p2k16Header", p2k16HeaderDirective);
})();
