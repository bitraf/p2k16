(function () {

    function config($routeProvider, $httpProvider, StripeCheckoutProvider) {

        /**
         *
         * @param {SmartCache} Circles
         */
        function circles(Circles) {
            // console.log("circles()");
            return Circles.promise();
        }

        function circle($route, Circles) {
            var circle_id = $route.current.params.circle_id;
            // console.log("circle(" + circle_id + ")");

            return Circles.promise().then(function (circles) {
                // console.log("return: circles", circles.by_key[circle_id]);
                return circles.by_key[circle_id];
            });
        }

        $routeProvider.when("/public/unauthenticated", {
            controller: UnauthenticatedController,
            controllerAs: 'ctrl',
            templateUrl: p2k16_resources.unauthenticated_html
        }).when("/", {
            controller: FrontPageController,
            controllerAs: 'ctrl',
            templateUrl: p2k16_resources.front_page_html,
            resolve: {
                recent_events: CoreDataServiceResolvers.recent_events
            }
        }).when("/about", {
            controller: AboutController,
            controllerAs: 'ctrl',
            templateUrl: p2k16_resources.about_html
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
        }).when("/tool", {
            controller: ToolFrontPageController,
            controllerAs: 'ctrl',
            templateUrl: p2k16_resources.tool_front_page_html,
            resolve: {
                tools: ToolDataServiceResolvers.data_tool_list,
                recent_events: ToolDataServiceResolvers.recent_events
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
                circles: circles
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
                circles: circles
            }
        }).when("/admin/circle/new", {
            controller: AdminCircleDetailController,
            controllerAs: 'ctrl',
            templateUrl: p2k16_resources.admin_circle_detail_html,
            resolve: {
                circles: circles,
                circle: _.constant({})
            }
        }).when("/admin/circle/:circle_id", {
            controller: AdminCircleDetailController,
            controllerAs: 'ctrl',
            templateUrl: p2k16_resources.admin_circle_detail_html,
            resolve: {
                circles: circles,
                // TODO: use the circle from the cache, look up members
                // circle: circle
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
        }).when("/admin/tool", {
            controller: AdminToolListController,
            controllerAs: 'ctrl',
            templateUrl: p2k16_resources.admin_tool_list_html,
            resolve: {
                tools: ToolDataServiceResolvers.data_tool_list
            }
        }).when("/admin/tool/new", {
            controller: AdminToolDetailController,
            controllerAs: 'ctrl',
            templateUrl: p2k16_resources.admin_tool_detail_html,
            resolve: {
                tools: ToolDataServiceResolvers.data_tool_list,
                tool: _.constant({})
            }
        }).when("/admin/tool/:tool_id", {
            controller: AdminToolDetailController,
            controllerAs: 'ctrl',
            templateUrl: p2k16_resources.admin_tool_detail_html,
            resolve: {
                tools: ToolDataServiceResolvers.data_tool_list,
                // TODO: use the circle from the cache, look up members
                // circle: circle
                tool: ToolDataServiceResolvers.data_tool
            }
        }).otherwise("/");

        $httpProvider.interceptors.push('P2k16HttpInterceptor');

        StripeCheckoutProvider.defaults({
            key: window.stripe_pubkey
        });
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
    function Log(name) {
        function info() {
            console.info.apply(console, [name].concat(Array.prototype.slice.call(arguments)));
        }

        function debug() {
            console.debug.apply(console, [name].concat(Array.prototype.slice.call(arguments)));
        }

        /**
         * @lends Log.prototype
         */
        return {
            d: debug,
            i: info
        }
    }

    /**
     * A not so very smart cache of items.
     *
     * Exposes two read-only (not enforced) data structures:
     *  - "by_key": a key-index map
     *  - "values": an array of all values
     *
     * Values retrieved from the cache are always valid and only their contents will be replaced if they are
     * refreshed with new data.
     *
     * @constructor
     */
    function SmartCache($q, name, params) {

        function defaultMapper(o) {
            return {key: o.id, value: o};
        }

        /**
         * @constructor
         */
        function Item(key, value, index) {
            this.key = key;
            this.value = value;
            this.index = index;
        }

        var mapper = params.mapper || defaultMapper;

        var l = new Log("SmartCache:" + name);
        var items = {};
        var itemCount = 0;
        // Values indexed by their key
        var by_key = {};
        // Unsorted array with all values
        var values = [];

        function put(value) {
            var mapped = mapper(value);
            var key = mapped.key;
            value = mapped.value;

            var item = items[key];

            var obj;
            if (item) {
                l.d("Replacing existing item", key);
                obj = item.value;
                for (var prop in obj) {
                    if (obj.hasOwnProperty(prop)) {
                        delete obj[prop];
                    }
                }
            } else {
                l.d("Creating new item", key);
                obj = {};
                var item = new Item(key, obj, itemCount++);
                items[key] = item;

                by_key[key] = obj;
                values[item.index] = obj;
            }

            _.assign(obj, value);
        }

        var currentPromise = null;

        function promise() {
            // l.i("promise()");
            var deferred = $q.defer();

            deferred.resolve(instance);

            return deferred.promise;
        }

        function executeControl(control) {
            l.d("Executing control", control.type);
            if (control.type === "replace-collection") {
                // l.d("Replacing collection");
                _.forEach(control.data, function (updated) {
                    put(updated);
                });
                // } else if (control.type === "invalidate-collection") {
            } else {
                l.i("Unsupported control type", control.type)
            }
        }

        /**
         * @lends SmartCache.prototype
         */
        var instance = {
            promise: promise,
            executeControl: executeControl,
            put: put,
            values: values,
            by_key: by_key,
            getName: function () {
                return name;
            }
        };

        return instance;
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
     * @param $rootScope
     * @param {SmartCache} Circles
     * @param {SmartCache} BadgeDescriptions
     * @constructor
     */
    function P2k16($rootScope, Circles, BadgeDescriptions) {
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
            return _.indexOf(self.circlesWithAdminAccess, circleId) !== -1;
        }

        if (window.p2k16.account) {
            setLoggedIn(window.p2k16.account);
        }

        self.circlesWithAdminAccess = window.p2k16.circlesWithAdminAccess || [];
        Circles.executeControl({type: "replace-collection", data: window.p2k16.circles || []});
        BadgeDescriptions.executeControl({type: "replace-collection", data: window.p2k16.badgeDescriptions || []});
        self.stripe_pubkey = window.p2k16.stripe_pubkey || "";

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
            stripe_pubkey: self.stripe_pubkey,
            messages: self.messages,

            canAdminCircle: canAdminCircle
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
            scope: {active: '@'},
            controller: p2k16HeaderController,
            controllerAs: 'header',
            templateUrl: p2k16_resources.p2k16_header_html
        }
    }

    function p2k16EntityInfo() {
        function ctrl() {
            this.show = function (entity) {
                if (!entity || !entity.createdAt || !entity.updatedAt) {
                    return false;
                }
                return entity.createdAt.substring(0, 19) !== entity.updatedAt.substring(0, 19);
            }
        }

        return {
            restrict: 'E',
            scope: {
                entity: '='
            },
            controller: ctrl,
            controllerAs: "ctrl",
            template: '<p ng-if="entity.id" class="text-muted entity-info">Created by {{ entity.createdBy }} at {{ entity.createdAt|date:\'medium\' }}<span\n' +
                'ng-if="ctrl.show(entity)">, last updated by {{ entity.updatedBy }} at\n{{ entity.updatedAt|date:\'medium\' }}</span>.</p>\n'
        }
    }

    function P2k16HttpInterceptor($rootScope, $q, P2k16, Circles, BadgeDescriptions) {

        function findCollection(name) {
            if (name === "circles") {
                return Circles;
            } else if (name === "badge-descriptions") {
                return BadgeDescriptions;
            }
        }

        return {
            response: function (res) {
                if (res && res.data && res.data._controls) {
                    // console.log("controls", res.data._controls);
                    _.forEach(res.data._controls, function (c) {
                        var collection = findCollection(c.collection);
                        collection.executeControl(c);
                    });
                }
                return res;
            },
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

    function YesNoFilter() {
        return function (b) {
            return b ? 'Yes' : 'No';
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

        self.activeMember = P2K16.currentAccount().active_member;
        self.doorsAvailable = selc.activeMember && 2k16.hasRole("door");

        self.recent_events = recent_events;
    }

    function AboutController() {
        var self = this;

        self.gitRevision = window.gitRevision;
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
     * @param {CoreDataService} CoreDataService
     * @param badgeDescriptions
     * @constructor
     */
    function MyProfileController($scope, P2k16, CoreDataService, badgeDescriptions) {
        var self = this;

        P2k16.accountListeners.add($scope, function (newValue) {
            console.log("updated", newValue);
            updateBadges(newValue);
        });

        function updateBadges(account) {
            self.badges = _.values(account.badges);
        }

        function changePassword() {
            CoreDataService.service_set_password(self.changePasswordForm).then(function (res) {
                var msg = res.message || "Password changed";
                P2k16.addInfos(msg);
            });
        }

        self.badges = [];
        self.newBadge = {};
        self.descriptions = badgeDescriptions;
        self.changePasswordForm = {};
        self.changePassword = changePassword;

        updateBadges(P2k16.currentAccount());
    }

    /**
     * @param $scope
     * @param {P2k16} P2k16
     * @param ToolDataService
     * @constructor
     */
    function ToolFrontPageController(ToolDataService, $scope, P2k16, tools, recent_events) {
        var self = this;

        self.recent_events = recent_events;

        self.my_account = P2k16.currentAccount().id;

        function update(data) {
            self.tools = data;
        }

        update(tools);

        self.checkoutTool = function (tool) {
            ToolDataService.checkout_tool({'tool': tool.id}).then(function (res) {
                console.log('checkout succeded', tool);
                update(res.data);
            })
        };

        self.checkinTool = function (tool) {
            ToolDataService.checkin_tool({'tool': tool.id}).then(function (res) {
                console.log('checkin succeded', tool);
                update(res.data);
            })
        };
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
     * @param {SmartCache} circles
     * @constructor
     */
    function AdminAccountDetailController($http, CoreDataService, account, circles) {
        var self = this;

        self.account = account;
        self.circles = _.filter(circles.values, function (c) {
            return !!_.find(self.account.circles, {id: c.id})
        });
        self.comment = "";
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
     * @param {SmartCache} circles
     * @constructor
     */
    function AdminCircleListController(CoreDataService, circles) {
        var self = this;

        self.circles = circles.values;
    }

    /**
     * @param $location
     * @param {CoreDataService} CoreDataService
     * @param {SmartCache} circles
     * @param circle
     * @constructor
     */
    function AdminCircleDetailController($location, CoreDataService, circles, circle) {
        var self = this;

        self.isNew = !circle.id;

        self.circleName = circle.id ? circle.name : "New circle";

        self.addCircleForm = {commentRequiredForMembership: false};
        self.addMemberForm = {username: "", comment: ""};

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
            }

            if (self.circle.adminCircle) {
                self.adminCircle = circles.by_key[self.circle.adminCircle];
            }
        }

        update(circle);

        self.createCircle = function () {
            CoreDataService.create_circle(self.addCircleForm).then(function (res) {
                $location.url("/admin/circle/" + res.data.id);
            });
        };
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
                circleId: self.circle.id,
                comment: self.addMemberForm.comment
            };
            self.addMemberForm.username = ""; // Keep the comment to make it easier to do bulk adds
            CoreDataService.add_account_to_circle(form).then(function (res) {
                update(res.data);
            });
        };
        self.selfAdminSelected = function () {
            if (!self.addCircleForm.comment && self.addCircleForm.commentRequiredForMembership) {
                self.addCircleForm.comment = 'Initial admin';
            }
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
     * @param {CoreDataService} CoreDataService
     * @param {SmartCache} tools
     * @constructor
     */
    function AdminToolListController(ToolDataService, tools) {
        var self = this;

        self.tools = tools;
    }

    /**
     * @param $location
     * @param {CoreDataService} CoreDataService
     * @param {SmartCache} circles
     * @param circle
     * @constructor
     */
    function AdminToolDetailController($location, ToolDataService, tools, tool) {
        var self = this;

        self.isNew = !tool.id;

        function setTool(tool) {
            self.tool = angular.copy(tool);
            isNew = !self.tool.id;
            self.title = isNew ? "New tool" : self.tool.name;
        }

        setTool(tool);

        self.save = function () {
            var q = self.tool.id
                ? ToolDataService.data_tool_update(self.tool)
                : ToolDataService.data_tool_add(self.tool);

            q.then(function (res) {
                if (isNew) {
                    $location.url("/admin/tool/" + res.data.id);
                } else {
                    setTool(res.data);
                    self.form.$setPristine();
                }
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

    function configSmartCaches($provide) {
        function valueMapper(circle) {
            circle._embedded = undefined;
            return {key: circle.id, value: circle};
        }

        $provide.factory("Circles", function ($q) {
            return new SmartCache($q, "Circle", valueMapper);
        });
        $provide.factory("BadgeDescriptions", function ($q) {
            return new SmartCache($q, "BadgeDescription", valueMapper);
        });
    }

    angular.module('p2k16.app', ['ngRoute', 'ui.bootstrap', 'stripe.checkout'])
        .config(configSmartCaches)
        .config(config)
        .run(run)
        .service("P2k16", P2k16)
        .service("BadgeDataService", BadgeDataService)
        .service("CoreDataService", CoreDataService)
        .service("DoorDataService", DoorDataService)
        .service("ToolDataService", ToolDataService)
        .service("AuthzService", AuthzService)
        .service("P2k16HttpInterceptor", P2k16HttpInterceptor)
        .filter("yesno", YesNoFilter)
        .directive("p2k16Header", p2k16HeaderDirective)
        .directive("p2k16EntityInfo", p2k16EntityInfo);
})();
