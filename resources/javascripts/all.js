jQuery.noConflict();

jQuery(function(){
    jQuery('[data-toggle="popover"]').popover({});
    jQuery('body').tooltip({
        'selector': '[data-toggle="tooltip"]'
    });
    jQuery('th input[type="checkbox"]').click(function(){
        var $this = jQuery(this);
        $this.closest(
            'table'
        ).find(
            'td input[type="checkbox"]'
        ).prop(
            'checked', $this.is(':checked')
        );
    });
    if (jQuery('#tour').length) {
        var tour = new Tour({
            'backdrop': true,
            'steps': [{
                'content': 'You may assign each recipe to a pack. These are created in the "Recipe Packs" section listed under "My Recipes" in the navigation bar. Packs are used to keep your recipes organized, and will allow you to share all recipes in a pack with other Mail Sidekick users in the future.',
                'element': '#pack',
                'placement': 'bottom',
                'title': 'Pack'
            }, {
                'content': 'Choose a name for your recipe. This will help you organize your campaigns in the overview page. Where you are able to change the order in which Mail Sidekick will process Recipes.',
                'element': '#name',
                'placement': 'bottom',
                'title': 'Name'
            }, {
                'content': 'You may describe your recipe in this field.',
                'element': '#description',
                'placement': 'bottom',
                'title': 'Description'
            }, {
                'content': 'These are the email accounts that you wish to apply this recipe to. You may apply the same recipe to as many email accounts as you\'d like, Mail Sidekick will process them all simultaneously. This feature is especially useful when you\'re running the same campaign across many email accounts.',
                'element': '#accounts-0',
                'placement': 'bottom',
                'title': 'Account(s)'
            }, {
                'content': 'The Reserved Period is used to prevent the sending of duplicate messages to the same person. If you receive multiple emails from the same user within the specified reserved period, you will not trigger the recipe again.',
                'element': '#visibility',
                'placement': 'bottom',
                'title': 'Reserved Period'
            }, {
                'content': 'A schedule may be used in the event that you only want your outgoing emails to be delivered during certain times and/or days. This is useful when you\'re replying during business hours, or you\'ve found that your conversion rates are higher in the morning versus the evening.',
                'element': '#schedule',
                'placement': 'bottom',
                'title': 'Schedule'
            }, {
                'content': 'Conditions must be met for your recipe to trigger. If you have no conditions, your recipe will trigger on any received email. For example, if you only want to reply to emails with specific words in the subject, you may specify them here.',
                'element': '#conditions',
                'placement': 'bottom',
                'title': 'Condition(s)'
            }, {
                'content': 'Each step represents a single email to be sent. If you\'d like to respond to the same person more than once then you would create a step for each desired response. TIP: A followup one week after your first email response often results in additional conversions for Mail Sidekick campaigns designed around CPA offers.',
                'element': '#steps',
                'placement': 'bottom',
                'title': 'Step(s)'
            }, {
                'content': 'And you\'re done! Once you\'ve built the perfect recipe for your campaign, use the Submit button to save it.',
                'element': '#submit',
                'placement': 'bottom',
                'title': 'Submit'
            }],
            'storage': false,
            'template': jQuery('#tour .hide.template').html()
        });
        tour.init();
        tour.start();
    }
    jQuery('#two').slider({
        'min': 1,
        'tooltip': 'hide',
        'value': 1
    }).on('slide', function (event) {
        jQuery(this).parent().find('.round').html(event.value);
    });
    if (
        jQuery('.btn.btn-mini.btn-danger.survey').length
        &&
        !jQuery('#one, #two, #three').length
    ) {
        if (!jQuery.cookie('survey')) {
            jQuery.cookie('survey', 'survey', {
                'expires': 1
            });
            jQuery('#survey').modal();
        }
    }
    var clock = jQuery('.clock');
    clock.FlipClock(parseInt(clock.attr('data-seconds'), 10), {
        'clockFace': 'DailyCounter',
        'countdown': true
    });
});

var is_mahendra = function(){
    if(window.location.host == '127.0.0.1:5000'){
        return true;
    }
    return false;
};

var application = angular.module('application', []);

application.config(function ($httpProvider) {
    $httpProvider.defaults.headers.post[
        'Content-Type'
    ] = 'application/x-www-form-urlencoded';
});

application.config(function ($interpolateProvider) {
    $interpolateProvider.startSymbol('[!').endSymbol('!]');
});

application.controller(
    'account',
    [
        '$attrs',
        '$scope',
        function ($attrs, $scope) {
            $scope.account = jQuery.parseJSON($attrs.account);

            $scope.services = {
                'AOL': {
                    'incoming_hostname': 'imap.aol.com',
                    'incoming_port_number': '993',
                    'incoming_use_ssl': true,
                    'outgoing_hostname': 'smtp.aol.com',
                    'outgoing_port_number': '587',
                    'outgoing_use_ssl': false,
                    'outgoing_use_tls': true,
                    'username': '@aol.com'
                },
                'Gmail': {
                    'incoming_hostname': 'imap.gmail.com',
                    'incoming_port_number': '993',
                    'incoming_use_ssl': true,
                    'outgoing_hostname': 'smtp.gmail.com',
                    'outgoing_port_number': '465',
                    'outgoing_use_ssl': true,
                    'outgoing_use_tls': true,
                    'username': '@gmail.com'
                },
                'GoDaddy': {
                    'incoming_hostname': 'imap.secureserver.net',
                    'incoming_port_number': '993',
                    'incoming_use_ssl': true,
                    'outgoing_hostname': 'smtpout.secureserver.net',
                    'outgoing_port_number': '465',
                    'outgoing_use_ssl': true,
                    'outgoing_use_tls': true,
                    'username': ''
                },
                'HostGator': {
                    'incoming_hostname': 'mail.domain.com',
                    'incoming_port_number': '993',
                    'incoming_use_ssl': true,
                    'outgoing_hostname': 'mail.domain.com',
                    'outgoing_port_number': '26',
                    'outgoing_use_ssl': true,
                    'outgoing_use_tls': true,
                    'username': '@domain.com'
                },
                'Namecheap': {
                    'incoming_hostname': 'oxmail.registrar-servers.com',
                    'incoming_port_number': '993',
                    'incoming_use_ssl': true,
                    'outgoing_hostname': 'oxmail.registrar-servers.com',
                    'outgoing_port_number': '465',
                    'outgoing_use_ssl': true,
                    'outgoing_use_tls': true,
                    'username': ''
                },
                'Windows Live Hotmail': {
                    'incoming_hostname': 'pop3.live.com',
                    'incoming_port_number': '995',
                    'incoming_use_ssl': true,
                    'outgoing_hostname': 'smtp.live.com',
                    'outgoing_port_number': '587',
                    'outgoing_use_ssl': true,
                    'outgoing_use_tls': true,
                    'username': ''
                },
                'Yahoo! Mail': {
                    'incoming_hostname': 'imap.mail.yahoo.com',
                    'incoming_port_number': '993',
                    'incoming_use_ssl': true,
                    'outgoing_hostname': 'smtp.mail.yahoo.com',
                    'outgoing_port_number': '465',
                    'outgoing_use_ssl': true,
                    'outgoing_use_tls': true,
                    'username': '@yahoo.com'
                }
            };

            $scope.update = function (service) {
                $scope.account = $scope.services[service];
            };
        }
    ]
);

application.controller(
    'attachments',
    [
        '$element',
        '$scope',
        function ($element, $scope) {
            $scope.attachments = $scope.step.attachments || [];

            $scope.operand_1 = [
                'Name',
                'Extension',
                'Count',
                'Size',
            ];

            $scope.operator = [
                'is',
                'contains',
                'does not contain',
                'has all these words',
                'has atleast one of these words',
                'has none of these words',
                'is greater than',
                'is equal to',
                'is lesser than',
                'is not greater than',
                'is not equal to',
                'is not lesser than',
            ];

            $scope.qualities = [
                'Bytes',
                'KiB',
                'kB',
                'MiB',
                'MB',
            ];

            $scope.quantity = 0;
            $scope.quality = $scope.qualities[0];

            $scope.add = function () {
                $scope.attachments.push({
                    'operand_1': $scope.operand_1[0],
                    'operand_2': '',
                    'operator': $scope.operator[0]
                });
            };

            $scope.delete = function (attachment) {
                $scope.attachments.splice(
                    $scope.attachments.indexOf(attachment), 1
                );
            };

            $scope.open = function (index) {
                $scope.index = index;
                jQuery($element).find('.modal').modal('show');
            };

            $scope.close = function () {
                var value = $scope.quantity;
                switch ($scope.quality) {
                    case 'Bytes':
                        value = $scope.quantity;
                        break;
                    case 'KiB':
                        value = $scope.quantity * 1024;
                        break;
                    case 'kB':
                        value = $scope.quantity * 1000;
                        break;
                    case 'MiB':
                        value = $scope.quantity * 1024 * 1024;
                        break;
                    case 'MB':
                        value = $scope.quantity * 1000 * 1000;
                        break;
                    default:
                        value = $scope.quantity;
                        break;
                }
                $scope.attachments[$scope.index].operand_2 = value;
                jQuery($element).find('.modal').modal('hide');
            };


            $scope.$watch('attachments', function (new_value, old_value) {
                var attachments = [];
                jQuery.each($scope.attachments, function (key, value) {
                    if (
                        value.operand_1.length
                        &&
                        value.operator.length
                        &&
                        value.operand_2.length
                    ) {
                        attachments.push({
                            'operand_1': value.operand_1,
                            'operand_2': value.operand_2,
                            'operator': value.operator
                        });
                    }
                });
                jQuery($element).find('[name="attachments"]').val(
                    JSON.stringify(attachments)
                );
            }, true);
        }
    ]
);

application.controller(
    'code',
    [
        '$element',
        '$scope',
        function ($element, $scope) {
            var refresh = function(checkbox) {
                var checkboxes = checkbox.parent().parent().find(
                    'ul :checkbox'
                );
                if (checkboxes.length) {
                    if (checkbox.is(':checked')) {
                        checkboxes.attr('checked', true);
                        checkboxes.attr('disabled', true);
                    } else {
                        checkboxes.attr('disabled', false);
                    }
                }
            };

            $scope.click = function($event) {
                var $this = jQuery($event.target);
            };

            jQuery($element).find(':checkbox:checked').each(function () {
                refresh(jQuery(this));
            });
        }
    ]
);

application.controller(
    'conditions',
    [
        '$attrs',
        '$scope',
        function ($attrs, $scope) {
            $scope.conditions = jQuery.parseJSON($attrs.conditions) || [];

            $scope.operand_1 = [
                'From Address',
                'Subject',
                'Body',
            ];

            $scope.operator = [
                'is',
                'contains',
                'does not contain',
                'has all these words',
                'has atleast one of these words',
                'has none of these words',
            ];

            $scope.status = false;

            $scope.add = function () {
                $scope.conditions.push({
                    'operand_1': $scope.operand_1[0],
                    'operand_2': '',
                    'operator': $scope.operator[0]
                });
            };

            $scope.delete = function (condition) {
                $scope.conditions.splice(
                    $scope.conditions.indexOf(condition), 1
                );
                if ($scope.conditions.length == 0) {
                    $scope.status = false;
                }
            };

            $scope.profanity = function (condition) {
                $scope.conditions[$scope.conditions.indexOf(
                    condition
                )]['operand_2'] = '{{ profanity }}';
            };

            $scope.$watch('status', function (new_value, old_value) {
                if (new_value) {
                    if ($scope.conditions.length == 0) {
                        $scope.add();
                    }
                }
            });

            if ($scope.conditions.length) {
                $scope.status = true;
            }
        }
    ]
);

application.controller('filters', ['$scope', function ($scope) {
    $scope.status = false;
}]);

application.controller(
    'history',
    [
        '$attrs',
        '$element',
        '$http',
        '$scope',
        '$timeout',
        function ($attrs, $element, $http, $scope, $timeout) {
            var seconds = 10;

            $scope.items = [];
            $scope.seconds = 0;

            var refresh = function() {
                if ($scope.seconds == 0) {
                    $http({
                        'method': 'POST',
                        'url': $attrs.url
                    }).
                    error(function (data, status, headers, config) {
                        $scope.seconds = seconds;
                        $timeout(refresh, 1000);
                    }).
                    success(function (data, status, headers, config) {
                        $scope.items = data.items;
                        $scope.seconds = seconds;
                        $timeout(refresh, 1000);
                    });
                    return;
                }
                $scope.seconds -= 1;
                $timeout(refresh, 1000);
            };

            refresh();
        }
    ]
);

application.controller(
    'overview',
    [
        '$attrs',
        '$element',
        '$scope',
        function ($attrs, $element, $scope) {
            $scope.caption = $attrs.caption;
            $scope.items = [];

            $scope.delete = function () {
                jQuery($element).find('[value="delete"]').click();
            };

            $scope.process = function (e, status) {
                if (status) {
                    jQuery($element).find('.modal').modal('hide');
                    $scope.delete();
                    return;
                }
                $scope.items = [];
                jQuery($element).find('td :checkbox:checked').each(function () {
                    $scope.items.push(jQuery(this).attr('data-caption'));
                });
                if (!$scope.items.length) {
                    $scope.delete();
                    return;
                }
                jQuery($element).find('.modal').modal();
            };
        }
    ]
);

application.controller(
    'schedule',
    [
        '$attrs', '$element', '$scope', function ($attrs, $element, $scope) {
            $scope.days = jQuery.parseJSON($attrs.days);
            $scope.names = [
                'Monday',
                'Tuesday',
                'Wednesday',
                'Thursday',
                'Friday',
                'Saturday',
                'Sunday'
            ];

            var get_value = function (value) {
                return (
                    value < 12?
                    ((value > 0? value: 12) + 'AM'):
                    ((value - 12 > 0? value - 12: 12) + 'PM')
                );
            };

            $scope.add = function (index, hour) {
                $scope.days[index].push(hour);
            };

            $scope.click = function (index, hour) {
                hour = parseInt(hour, 10);
                if ($scope.days[index].indexOf(hour) === -1) {
                    $scope.add(index, hour);
                } else {
                    $scope.delete(index, hour);
                }
                $scope.refresh();
            };

            $scope.delete = function (index, hour) {
                $scope.days[index].splice($scope.days[index].indexOf(hour), 1);
            };

            $scope.invert = function (index) {
                for (var hour = 0; hour <= 23; hour += 1) {
                    $scope.click(index, hour)
                }
                $scope.refresh();
            };

            $scope.range = function (start, stop, step) {
                var items = [];
                for (var index = start; index < stop; index = index + step) {
                    items.push(index);
                }
                return items;
            };

            $scope.refresh = function () {
                jQuery($element).find('[name="schedule_days"]').val(
                    JSON.stringify($scope.days)
                );
            };

            $scope.toggle = function (index) {
                if ($scope.days[index].length) {
                    $scope.days[index] = [];
                } else {
                    $scope.days[index] = [];
                    for (var hour = 0; hour <= 23; hour += 1) {
                        $scope.add(index, hour);
                    }
                }
                $scope.refresh();
            };

            $scope.get_class = function (index, hour) {
                hour = parseInt(hour, 10);
                if ($scope.days[index].indexOf(hour) !== -1) {
                    return 'active';
                }
                return '';
            };

            $scope.get_hours = function () {
                return $scope.days.reduce(
                    function(previous, current, index, array){
                        return previous + current.length;
                    },
                0);
            };

            $scope.get_string = function (index) {
                var timezone = jQuery($element).find('select').val();
                var hours = $scope.days[index];
                if (hours.length == 24) {
                    return (
                        get_value(0) + ' ' + timezone +
                        ' to ' +
                        get_value(23) + ' ' + timezone
                    );
                }
                if (hours.length == 0) {
                    return 'Do Not Send';
                }
                hours.sort(function(a, b) {
                    return a - b;
                });
                var segments = [];
                segments.push([]);
                jQuery.each(hours, function (key, value) {
                    if (key != 0 && value != hours[key - 1] + 1) {
                        segments.push([]);
                    }
                    segments[segments.length - 1].push(value);
                });
                jQuery.each(segments, function (key, value) {
                    if (value.length > 1) {
                        value = (
                            get_value(value[0]) + ' ' + timezone +
                            ' to ' +
                            get_value(value[value.length - 1]) + ' ' +
                            timezone
                        );
                    } else {
                        if (value.length == 1) {
                            value = get_value(value[0]) + ' ' + timezone;
                        } else {
                            value = '';
                        }
                    }
                    segments[key] = value;
                });
                segments = segments.filter(function (value) {
                    return value.length;
                });
                return segments.join(', ');
            };

            jQuery($element).on('change click', 'select', function () {
                $scope.$digest();
            });

            $scope.refresh();
        }
    ]
);

application.controller(
    'steps',
    [
        '$attrs',
        '$element',
        '$scope',
        '$timeout',
        function ($attrs, $element, $scope, $timeout) {
            $scope.accounts = jQuery.parseJSON($attrs.accounts) || [];
            $scope.delay_units = [
                'Minutes',
                'Hours',
                'Days',
            ];
            $scope.templates = jQuery.parseJSON($attrs.templates) || [];
            $scope.steps = jQuery.parseJSON($attrs.steps) || [];

            $scope.process = function (routine) {
                var phase = this.$root.$$phase;
                if (phase == '$apply' || phase == '$digest') {
                    $timeout(click, 1);
                    return;
                }
                this.$apply(routine);
            };

            $scope.add = function () {
                $scope.steps.push({
                    'account': '0',
                    'delay_quantity': '0',
                    'delay_unit': $scope.delay_units[0],
                    'number_of_days': '0',
                    'number_of_emails': '0',
                    'reply_to_email': '',
                    'reply_to_name': '',
                    'templates': []
                });
                $scope.process(click);
            };

            $scope.delete = function (step) {
                $scope.steps.splice(
                    $scope.steps.indexOf(step), 1
                );
                $scope.process(click);
            };

            $scope.get_account = function (index) {
                var account = get_tab(index).find('[name="account"]').prev();
                if (account.val() == '0') {
                    return 'the original account';
                }
                return jQuery.trim(jQuery(account).find(':selected').text());
            };

            $scope.get_template = function (index) {
                var inputs = get_tab(
                    index
                ).find('[name="templates_' + index + '"]:checked');
                if (!inputs.length) {
                    return 'a randomly selected template';
                }
                if (inputs.length == 1) {
                    return 'the template ' + jQuery.trim(jQuery(
                        inputs[0]
                    ).parent().text());
                }
                var templates = [];
                jQuery(inputs).each(function () {
                    templates.push(jQuery.trim(jQuery(this).parent().text()));
                });
                return 'a randomly selected template (among ' +  templates.join(
                    ', '
                ) + ')';
            };

            var click = function () {
                jQuery($element).find('ul li a:last').click();
            };

            var get_tab = function (index) {
                return jQuery($element).find('#tab_' + (index + 1));
            };

            if ($scope.steps.length == 0) {
                $scope.add();
            }

            jQuery($element).on('change click', ':checkbox', function () {
                $scope.$digest();
            });
        }
    ]
);

application.controller(
    'videos',
    [
        '$element',
        '$scope',
        function ($element, $scope) {
            $scope.close = function () {
                jQuery($element).find('video').each(function () {
                    this.pause();
                });
                jQuery($element).find('.modal').modal('hide');
            };

            $scope.open = function () {
                jQuery($element).find('.modal').modal();
                jQuery($element).find('video').get(0).play();
            };
        }
    ]
);

application.directive('daterangepicker', function () {
    return {
        'link': function (scope, element, attrs) {
            var $this = jQuery(element).find('input');
            var end;
            var separator = ' to ';
            var start;
            if ($this.val()) {
                var dates = $this.val().split(separator);
                var start = dates[0];
                var end = dates[1];
            }
            $this.daterangepicker({
                'applyClass': 'btn-success',
                'buttonClasses': [
                    'btn'
                ],
                'clearClass': 'btn-danger',
                'endDate': end,
                'format': 'YYYY-MM-DD',
                'locale': {
                    'applyLabel': 'Submit',
                    'customRangeLabel': 'Custom Range',
                    'daysOfWeek': [
                        'Sun',
                        'Mon',
                        'Tue',
                        'Wed',
                        'Thu',
                        'Fri',
                        'Sat'
                    ],
                    'firstDay': 1,
                    'monthNames': [
                        'January',
                        'February',
                        'March',
                        'April',
                        'May',
                        'June',
                        'July',
                        'August',
                        'September',
                        'October',
                        'November',
                        'December'
                    ]
                },
                'opens': 'left',
                'ranges': {
                    'Today': [
                        new Date(),
                        new Date()
                    ],
                    'Yesterday': [
                        moment().subtract('days', 1),
                        moment().subtract('days', 1)
                    ],
                    'Last 7 Days': [
                        moment().subtract('days', 6),
                        new Date()
                    ],
                    'Last 30 Days': [
                        moment().subtract('days', 29),
                        new Date()
                    ],
                    'This Month': [
                        moment().startOf('month'),
                        moment().endOf('month')
                    ],
                    'Last Month': [
                        moment().subtract('month', 1).startOf('month'),
                        moment().subtract('month', 1).endOf('month')
                    ]
                },
                'separator': separator,
                'startDate': start
            });
        },
        'restrict': 'A'
    };
});

application.controller('template', ['$scope', function ($scope) {
    $scope.items = {
        '0': '0',
        '1': '1',
        '2': '2'
    };

    $scope.add = function () {
        for (var index = 0; ; index += 1) {
            if (!(index.toString() in $scope.items)) {
                $scope.items[index.toString()] = index.toString();
                break;
            }
        }
    };

    $scope.delete = function (index) {
        delete $scope.items[index];
    };
}]);

application.directive('filestyle', function () {
    return {
        'link': function (scope, element, attrs) {
            jQuery(element).filestyle({
                'buttonText': 'Browse',
                'classButton': 'btn'
            });
        },
        'restrict': 'A'
    };
});

application.directive('wysihtml5', function () {
    return {
        'link': function (scope, element, attrs) {
            var stylesheets = [];
            jQuery('head > link').each(function () {
                stylesheets.push(jQuery(this).attr('href'));
            });
            jQuery(element).wysihtml5({
                'color': true,
                'emphasis': true,
                'font-styles': true,
                'html': true,
                'image': true,
                'link': true,
                'lists': true,
                'stylesheets': stylesheets,
                'useLineBreaks': false
            })
        },
        'restrict': 'A'
    };
});
