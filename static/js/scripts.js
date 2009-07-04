var cache = [];
var COLORS = [ 'green', 'orange', 'yellow', 'blue', 'purple'];
var COLOR = 0;
var PREFS = {};

var CACHE_TTL = 60 * 5; // 5 min
var last_sync_time = 0;

$(document).ready(function() {
    
    // aux functions 

    var display_group_name = function(name, trim) {
        name = name == '__ALL__' ? 'Uncategorized' : name;
        if (trim && name.length > 14)
            name = name.substring(0, 14) + '..';
        return name;
    }

    var render_group = function(g) {

        var container = $('<div class="group-background groupentry">').droppable({
            accept: '.userinfo', 
            drop: function(event, ui) {
                var dest = $('a', this).data('groupname');
                move_user(ui.draggable.get(0).id.substring(5), dest);
                $('a.grclosed-hl', $(this)).removeClass('grclosed-hl').addClass('grclosed');
                $('a.gropen-hl', $(this)).removeClass('gropen-hl').addClass('gropen');
            },
            over: function() {
                $('a.grclosed', $(this)).removeClass('grclosed').addClass('grclosed-hl');
                $('a.gropen', $(this)).removeClass('gropen').addClass('gropen-hl');
            },
            out: function() {
                $('a.grclosed-hl', $(this)).removeClass('grclosed-hl').addClass('grclosed');
                $('a.gropen-hl', $(this)).removeClass('gropen-hl').addClass('gropen');
            }
        });

        var c = COLORS[COLOR++];
        if (COLOR >= COLORS.length)
            COLOR = 0;
        var node = $('<a href="javascript:;" ' + (g.name != '__ALL__' ? '' : ' id="root"') + ' class="grclosed ' + c + '-sm color-' + c + '"></a>').attr({
        }).data('groupname', g.name).click(function(e) {
            open_group($(this));
            e.stopPropagation();
            e.preventDefault();
        });

        var span = $('<span>').text(display_group_name(g.name, true));

        container.append(node.append(span));

        if (g.name != '__ALL__') {
            var buttons = $('<div class="group-button">');
            var editbutton = $('<a href="javascript:;" title="Rename"></a>').click(function(e) {
                $('#old-group-name').val(g.name);
                $('#new-group-name').val(g.name);
                $('#rename-dialog').dialog('open');
                e.stopPropagation();
                e.preventDefault();
            }).append($('<img src="images/edit.png" alt="Rename"/>'));

            var delbutton = $('<a href="javascript:;" title="Delete"></a>').click(function(e) {
                delete_group(g.name);
                e.stopPropagation();
                e.preventDefault();
            }).append($('<img src="images/delete.png" alt="Delete"/>'));

            container.append(buttons.append(editbutton).append(delbutton));
        }

        $('#groups').append(container);
    };

    var render_user = function(u, g) {

        var picturebox = '<div class="userinfo_pic">' +
            '<b class="utop"><b class="ub1"></b><b class="ub2"></b><b class="ub3"></b><b class="ub4"></b></b>' +
            '<div class="userpic-box-content">' +
            '<img src="' + u.profile_image_url + '" alt="' + u.screen_name + '" width="48" height="48"/>' +
            '</div>' +
            '<b class="ubottom"><b class="ub4"></b><b class="ub3"></b><b class="ub2"></b><b class="ub1"></b></b>' +
            '</div>';

        var linkbox = '<div class="userinfo_screenname">' + u.screen_name + '</div>';

        var namebox = '<div class="userinfo_realname">' + (u.real_name == u.screen_name ? '&nbsp;' : u.real_name) + '</div>';

        var container   = $('<div id="user_' + u.screen_name + '" class="userinfo' + ($('#vs-icons').attr('checked') ? ' short_details' : '') + '">');
        container.append(picturebox).append(linkbox).append(namebox);

        var numgroups = 0;
        for (var i in cache) {
            numgroups++;
        }

        var controls = $('<div class="user-edit-buttons">');

        if (numgroups > 1) {
            controls.append($('<a href="javascript:;" title="Move"><img src="images/move.png" alt="Move"></a>').click(function(e) {
                $('#user-to-move').val(u.screen_name);
                $('#user-to-move-name').text(u.real_name);
                var groups = $('#group-to-move');
                groups.empty();
                for (var g in cache) {
                    if (g != $('#info_groupname').text()) {
                        groups.append($('<option>').attr('value', g).text(display_group_name(g)));
                    }
                }
                $('#move-dialog').dialog('open');
                e.stopPropagation();
                e.preventDefault();
            }));
        }
        controls.append($('<a href="http://twitter.com/' + u.screen_name + '" title="User Info" target="_blank"><img src="images/user.png" alt="Open"/></a>'));
        container.append(controls);

        container.draggable({appendTo : 'body',helper:'clone', start: function() {
                $('#tt').hide();
                $('.userinfo_pic').die('mouseover');        
            }, stop: function() {
                $('.userinfo_pic').live('mouseover', function(e) {
                show_tooltip(e, $(this));
            })
        }});
        $('#groupmembers').append(container);
    }

    var open_page = function(id) {
        if (id != 'manage' && id != 'prefs' || tweetonica.api.token) {
            $('.menu').removeClass('active');
            if (id == 'progress')
                $('#mmanage').addClass('active');
            else
                $('#m' + id).addClass('active');
            $('.page').hide();
            var p = $('#' + id);
            if (id != 'manage' && id != 'progress' && id != 'prefs')
               p.load(id + '.html');
            p.show();
        }
        else {
            document.location.href = '/oauth/login';
        }
    };

    var move_user = function(screen_name, group_name) {
        tweetonica.api.move_friend(screen_name, group_name, function(results) {
            var src = null;
            var destg = null;
            var srcg = null;
            for (var g in cache) {
                var info = cache[g];
                for (var i = 0; i < info.users.length; i++) {
                    if (info.users[i].screen_name == screen_name) {
                        src = info.users[i];
                        srcg = info;
                        info.users.splice(i, 1);
                        break;
                    }
                }
                if (info.name == group_name) {
                    destg = info;
                }
            }
            if (destg && src) {
                destg.users.push(src);
                if (destg.name != srcg.name)
                    $('#user_' + screen_name).remove();
            check_for_updates();
        }});
    };

    var delete_group = function(name) {
        $('#group-to-delete').val(name);
        $('#group-to-delete-name').text(name);
        $('#delete-confirm-dialog').dialog('open');
    }

    var create_group = function(name) {
        tweetonica.api.new_group(name, function(results) {
            var g = {name: name, users: [], rssurl: results.rssurl};
            cache[name] = g;
            render_group(g);
            open_group($('#groups a.gropen'));
            check_for_updates();
        });
    }

    var reset_prefs = function() {
        $('#prefs_remember_me').attr('checked', PREFS.remember_me === null || PREFS.remember_me === true ? 'checked' : null);
        $(':radio[name=prefs_auth_style]').val([PREFS.use_HTTP_auth === true ? '1' : '0']);
        $(':radio[name=prefs_icons_only]').val([PREFS.icons_only === true ? '1' : '0']);
    }

    var rename_group = function(old_name, new_name) {
        tweetonica.api.rename_group(old_name, new_name, function(results) {
            var tmp = [];
            for (var g in cache) {
                var info = cache[g];
                if (info.name == old_name) {
                    info.name = results.name;
                    info.rssurl = results.rssurl;
                }
                tmp[info.name] = info;
            }
            cache = tmp;
            $('#groups a').each(function() {
                var o = $(this);
                if (o.data('groupname') == old_name) {
                    o.data('groupname', new_name);
                    $('span', o).text(display_group_name(new_name, true));
                    open_group(o);
                }
            });
            check_for_updates();
        });
    }

    var open_group = function(e) {
        $('a.gropen').each(function() {
            var cl = this.className.split(' ');
            var newcl = 'grclosed ';
            for (var i = 0; i < cl.length; i++) {
                if (cl[i].indexOf('color-') == 0) {
                    newcl += cl[i] + ' ' + cl[i].substring(6) + '-sm';
                    break;
                }
            }
            this.className = newcl;
        });

        var cl = e.attr('className').split(' ');
        var newcl = 'gropen ';
        for (var i = 0; i < cl.length; i++) {
            if (cl[i].indexOf('color-') == 0) {
                newcl += cl[i] + ' ' + cl[i].substring(6) + '-bg';
                break;
            }
        }

        e.get(0).className = newcl;

        var g = cache[e.data('groupname')];
        $('#info_groupname').text(display_group_name(g.name));
        $('#info_groupfeed').attr('href', g.rssurl);
        $('#info_groupfeed_text').val(g.rssurl);

        $('#groupmembers').empty();
        for (var i = 0; i< g.users.length; i++) {
            render_user(g.users[i], g);
        }
    }

    var sync_groups = function(force, callback) {
         tweetonica.api.sync_friends(force, function(results) {
            if (callback)
                callback(results);
        }, function(error) {
            $.cookie('oauth.twitter', null, {expires: -1, path: '/'});
            $('#follow').hide();
            $('.prefsmenu').hide();
            open_page('about');
        });
    };

    var check_for_updates = function() {
        if ((new Date()).getTime() - last_sync_time > CACHE_TTL) {
            sync_groups(false, function(state) {
                if (state) {
                    open_page('progress');
                    refresh_groups(function() {
                        open_page('manage');
                    });
                } 
                else
                    last_sync_time = (new Date()).getTime();
            });
        }
    };

    var initialize = function(first) {

        open_page('progress');

        tweetonica.api.get_prefs(function(results) {
            PREFS = results;
            reset_prefs();
            if (first)
            {
                $('input[name=vs]').val([PREFS.icons_only === true ? '1' : '0']);
                $('#currentuser').text(results.screen_name);
                $('#currentuserurl').attr('href', 'http://twitter.com/' + results.screen_name);
                $('#loggedin').show();
                $('#loggedout').hide();
            }
            $('#opml_link').attr('href', results.OPML_download_url);
            $('#opml_text').val(results.OPML_feed_url);

            $('.prefsmenu').show();

            sync_groups(true, function(state) {
                refresh_groups(function() {
                    open_page('manage');
                });
            });
        }, function(error) {
            tweetonica.api.token = null;
            $.cookie('oauth.twitter', null, {expires: -1, path: '/'});
            $('#follow').hide();
            $('.prefsmenu').hide();
            open_page('about');
        });
    };

    var refresh_groups = function(callback) {
        tweetonica.api.get_friends(function(results) {
            last_sync_time = (new Date()).getTime();
            cache = {};

            var groups = [];
            for (var g in results) {
                groups.push(results[g]);
            }

            groups.sort(function(a, b) {
                if (a.name == '__ALL__')
                    return -1;
                if (b.name == '__ALL__')
                    return 1;
                var k1 = a.name.toLowerCase();
                var k2 = b.name.toLowerCase();
                return k1 > k2 ? 1 : k1 == k2 ? 0 : - 1;
            });
            cache = [];

            var follows_tweetonica = false;

            $('.groupentry').remove();
            for (var i = 0; i < groups.length; i++) {
                var group = groups[i];
                render_group(group);
                cache[group.name] = group;
                for (var j = 0; !follows_tweetonica && j < group.users.length; j++) {
                   if (group.users[j].screen_name == 'tweetonica') {
                       follows_tweetonica = true;
                       break;
                   }
                }
            }

            if (follows_tweetonica)
               $('#follow').hide();
            else
               $('#follow').show();

            open_group($('#groups a#root'));

            if (callback)
               callback();

        }, function(error) {
            $.cookie('oauth.twitter', null, {expires: -1, path: '/'});
            $('#follow').hide();
            $('.prefsmenu').hide();
            $('#currentuser').html('');
            $('#currentuserurl').attr('href', 'javascript:;');
            $('#loggedin').hide();
            $('#loggedout').show();
            tweetonica.api.token = null;

        });
    };

    $('#delete-confirm-dialog').dialog({
        buttons: {
            'Cancel': function() {
                $('#delete-confirm-dialog').dialog('close');
            },
            'OK': function() {
                var name = $('#group-to-delete').val();
                tweetonica.api.delete_group(name, function(results) {
                    var src = cache[name];
                    for (var i = 0; i < src.users.length; i++)
                        cache['__ALL__'].users.push(src.users[i]);                        

                    var tmp = [];
                    for (var g in cache) {
                        var info = cache[g];
                        if (info.name != name)
                            tmp[g] = info;                
                    }
                    cache = tmp;
                    $('#groups a').each(function() {
                        var o = $(this);
                        if (o.data('groupname') == name) {
                            o.parent().remove();
                        }
                    });
                    open_group($('#groups a#root'));
                    check_for_updates();
                });
                $('#delete-confirm-dialog').dialog('close');
            }
        },
        autoOpen: false,
        modal: true,
        resizable: false,
        title: 'Please confirm group deletion',
        width: 360
    });

    $('#move-dialog').dialog({
        buttons: {
            'Cancel': function() {
                $('#move-dialog').dialog('close');
            },
            'OK': function() {
                var screen_name = $('#user-to-move').val();
                var group_name  = $('#group-to-move').val();
                move_user(screen_name, group_name);
                $('#move-dialog').dialog('close');
            }
        },
        autoOpen: false,
        modal: true,
        resizable: false,
        title: 'Please select destination',
        width: 360
    });

    var rename_dialog_callback = function() {
        $('.error').hide();
        var old_name = $('#old-group-name').val();
        var new_name  = jQuery.trim($('#new-group-name').val());
        if (!new_name) {
            $('#eemptyname').show();
        } else {
            if (old_name == new_name) {
                $('#rename-dialog').dialog('close');
                return;
            }
            for (var g in cache) {
                if (g == new_name) {
                    $('#eduplicatename').show();
                    return;
                }
            }
            rename_group(old_name, new_name);
            $('#rename-dialog').dialog('close');
        }
    };

    $('#rename-dialog').dialog({
        buttons: {
            'Cancel': function() {
                $('#rename-dialog').dialog('close');
            },
            'OK': rename_dialog_callback
        },
        autoOpen: false,
        modal: true,
        resizable: false,
        title: 'Rename group',
        width: 360,
        open: function() {
            setTimeout(function() {$('#new-group-name').focus()}, 100);
        }
    });

    $('#new-group-name').keypress(function(e) {
        if (e.which == 13) {
            rename_dialog_callback();
            e.preventDefault();
            e.stopPropagation();
        }
    });


    var create_dialog_callback = function() {
        $('.error').hide();
        var name  = jQuery.trim($('#create-group-name').val());
        if (!name) {
            $('#eemptyname2').show();
        } else {
            for (var g in cache) {
                if (g == name) {
                    $('#eduplicatename2').show();
                    return;
                }
            }
            create_group(name);
            $('#create-dialog').dialog('close');
        }
    };

    $('#create-dialog').dialog({
        buttons: {
            'Cancel': function() {
                $('#create-dialog').dialog('close');
            },
            'OK': create_dialog_callback
        },
        autoOpen: false,
        modal: true,
        resizable: false,
        title: 'Create group',
        width: 360,
        open: function() {
            setTimeout(function() {$('#create-group-name').focus()}, 100);
        }
    });

    $('#create-group-name').keypress(function(e) {
        if (e.which == 13) {
            create_dialog_callback();
            e.preventDefault();
            e.stopPropagation();
        }
    });


    // handlers

    $('.menu').click(function(e) {
        var pageid = this.id.substring(1);
        open_page(pageid);
        e.stopPropagation();
        e.preventDefault();
    });

    $('.menulink').click(function(e) {
        var pageid = this.id.substring(2);
        $('#m' + pageid).click();
        e.stopPropagation();
        e.preventDefault();
    });


    $('#logoutbutton').click(function(e) {
        document.location.href = '/oauth/logout';
    });

    $('#loginbutton').click(function(e) {
        document.location.href = '/oauth/login';
    });

    $(':radio[name=vs]').click(function() {
        if ($('#vs-icons').attr('checked'))
            $('.userinfo').addClass('short_details');
        else
            $('.userinfo').removeClass('short_details');
    });

    $('.add-group a').click(function(e) {
        $('#create-group-name').val('');
        $('#create-dialog').dialog('open');
        e.stopPropagation();
        e.preventDefault();
    });

    $('#followme').click(function(e) {
        tweetonica.api.create_friendship('tweetonica', function(results) {
            cache['__ALL__'].users.push({screen_name: 'tweetonica', real_name: 'tweetonica', profile_image_url: '/images/twitter-logo.png'});
            open_group($('#groups a#root'));            
            $('#follow').hide();
            check_for_updates();
        }, function(error) {
        });
        e.stopPropagation();
        e.preventDefault();
    });

    var show_tooltip = function(e, o) {
        if (!$('#vs-icons').attr('checked'))
            return;
        $('#tt-screen').text($('.userinfo_screenname', o.parent()).text());
        var realname = jQuery.trim($('.userinfo_realname', o.parent()).text());
        if (realname != '')
            $('#tt-real').text(realname).show();
        else
            $('#tt-real').hide();
        var offset = o.offset();
        $('#tt').css('display','block').css('left', offset.left + o.width() / 2).css('top', offset.top - 30);
        e.stopPropagation();
        e.preventDefault();
    }

    $('.userinfo_pic').live('mouseover', function(e) {
        show_tooltip(e, $(this));
    }).live('mouseout', function(e) {
        $('#tt').css('display','none');
    });

    $('input[readonly]').click(function() {
        $(this).focus().select();
    });

    $('#btn-apply-prefs').click(function() {
        var temp_prefs = {};
        temp_prefs['remember_me'] = $('#prefs_remember_me').attr('checked') ? true : false;
        temp_prefs['use_HTTP_auth'] = $(':radio[name=prefs_auth_style]:checked').val() == '1' ? true : false;
        temp_prefs['icons_only'] = $(':radio[name=prefs_icons_only]:checked').val() == '1' ? true : false;

        tweetonica.api.set_prefs(temp_prefs, function(results) {
            PREFS = results; 
            $('#opml_link').attr('href', results.OPML_download_url);
            $('#opml_text').val(results.OPML_feed_url);
            open_page('progress');
            refresh_groups(function() {
                open_page('prefs');
            });
        }, function(error) {            
        });
    });

    $('#btn-reset-prefs').click(function() {
        reset_prefs();
    });

    $('#btn-sync-groups').click(function() {
        open_page('progress');
        sync_groups(true, function(state) {
            if (state) {
                refresh_groups(function() {
                    open_page('manage');
                });
            } else 
                open_page('manage');
        });
    });

    $('#btn-reset-token').click(function() {
        tweetonica.api.reset_RSS_token(function() {
            initialize(false);
        });
    });


    var cookie = $.cookie('oauth.twitter');
    if (cookie) {
        tweetonica.api.token = cookie;
        initialize(true);
    }
    else
        open_page('about');

});
