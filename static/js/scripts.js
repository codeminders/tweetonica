var cache = [];
var COLORS = [ 'green', 'orange', 'yellow', 'blue', 'purple'];
var COLOR = 0;

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
                var dest = $('a', this).attr('groupname');
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
        var node = $('<a href="javascript:;" class="grclosed ' + c + '-sm">').attr({
            groupname: g.name,
            colorname: c
        }).click(function(e) {
            open_group($(this));
            e.stopPropagation();
            e.preventDefault();
        });

        var span = $('<span>').text(display_group_name(g.name, true));

        container.append(node.append(span));

        if (g.name != '__ALL__') {
            var buttons = $('<div class="group-button">');
            var editbutton = $('<a href="javascript:;" title="Rename">').click(function(e) {
                $('#old-group-name').val(g.name);
                $('#new-group-name').val(g.name);
                $('#rename-dialog').dialog('open');
                e.stopPropagation();
                e.preventDefault();
            }).append($('<img src="images/edit.png" alt="Rename"/>'));

            var delbutton = $('<a href="javascript:;" title="Delete">').click(function(e) {
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

        var container   = $('<div id="user_' + u.screen_name + '" class="userinfo' + ($(':radio[name=viewstyle]:checked').val() == 's' ? ' short_details' : '') + '">');
        container.append(picturebox).append(linkbox).append(namebox).append('<div class="clear-div">&nbsp;</div>');

        var numgroups = 0;
        for (var i in cache) {
            numgroups++;
        }

        if (numgroups > 1) {
            var controls = $('<a href="javascript:;" title="Move"><img src="images/move.png" alt="Move"></a>').click(function(e) {
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
            });
            container.append(controls);
        }
        container.append($('<a href="http://twitter.com/' + u.screen_name + '" title="User Info" target="_blank"><img src="images/user.png" alt="Open"/></a>'));

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
        if (id != 'manage' || tweetonica.api.token) {
            $('.menu').removeClass('active');
            $('#m' + id).addClass('active');
            $('.page').hide();
            var p = $('#' + id);
            if (id != 'manage' && id != 'progress')
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
        });
    }

    var rename_group = function(old_name, new_name) {
        tweetonica.api.rename_group(old_name, new_name, function(results) {
            var tmp = [];
            for (var g in cache) {
                var info = cache[g];
                if (info.name == old_name) {
                    info.name = new_name;
                }
                tmp[info.name] = info;
            }
            cache = tmp;
            $('#groups a').each(function() {
                var o = $(this);
                if (o.attr('groupname') == old_name) {
                    o.attr('groupname', new_name);
                    $('span', o).text(display_group_name(new_name, true));
                    open_group(o);
                }
            });
        });
    }

    var open_group = function(e) {
        $('a.gropen').each(function() {
            $(this).attr('class', 'grclosed ' + $(this).attr('colorname') + '-sm');
        });
        e.attr('class', 'gropen ' + e.attr('colorname') + '-bg');

        var g = cache[e.attr('groupname')];
        $('#info_groupname').text(display_group_name(g.name));
        $('#info_groupfeed').attr('href', g.rssurl);
        $('#info_groupfeed_text').val(g.rssurl);

        $('#groupmembers').empty();
        for (var i = 0; i< g.users.length; i++) {
            render_user(g.users[i], g);
        }
    }

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
                        if (o.attr('groupname') == name) {
                            o.parent().remove();
                        }
                    });
                    open_group($('#groups a[groupname=__ALL__]'));
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

    $(':radio[name=viewstyle]').click(function() {
        if (this.value == 's')
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

    var cookie = $.cookie('oauth.twitter');
    if (cookie) {
        open_page('progress');

        tweetonica.api.token = cookie;
        tweetonica.api.get_screen_name(function(results) {
             $('#currentuser').html(results);
             $('#currentuserurl').attr('href', 'http://twitter.com/' + results);
             $('#loggedin').show();
             $('#loggedout').hide();

             tweetonica.api.sync_friends(true, function(results) {
                 tweetonica.api.get_friends(function(results) {

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

                     open_group($('#groups a[groupname=__ALL__]'));
                     open_page('manage');
                 }, function(error) {
                     $.cookie('oauth.twitter', null, {expires: -1, path: '/'});
                     $('#follow').hide();
                     $('#currentuser').html('');
                     $('#currentuserurl').attr('href', 'javascript:;');
                     $('#loggedin').hide();
                     $('#loggedout').show();
                     tweetonica.api.token = null;

                 });
            }, function(error) {
                $.cookie('oauth.twitter', null, {expires: -1, path: '/'});
                $('#follow').hide();
            });
        }, function(error) {
            $.cookie('oauth.twitter', null, {expires: -1, path: '/'});
            $('#follow').hide();
        });
    }
    else
        open_page('about');

    $('#followme').click(function(e) {
        tweetonica.api.create_friendship('tweetonica', function(results) {
            cache['__ALL__'].users.push({screen_name: 'tweetonica', real_name: 'tweetonica', profile_image_url: '/images/twitter-logo.png'});
            open_group($('#groups a[groupname=__ALL__]'));            
            $('#follow').hide();
        }, function(error) {
        });
        e.stopPropagation();
        e.preventDefault();
    });

    var show_tooltip = function(e, o) {
        if ($(':radio[name=viewstyle]:checked').val() != 's')
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



});
