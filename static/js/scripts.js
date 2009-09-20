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
        name = name == '__REPLIES__' ? 'Replies' : name;
        if (trim && name.length > 14)
            name = name.substring(0, 14) + '..';
        return name;
    }

    var display_unread = function(unread) {
        if (unread == 0) return '';
        return '('+unread+')';
    }
    
    var set_group_unread = function(group, unread) {
        $('.unread', group).text(display_unread(unread)).data('count', unread);
        if (unread == 0) group.removeClass('bold');
        else group.addClass('bold');
    }
    
    var update_title = function() {
        if ($('.act').attr('id') != 'mthreads') {
            document.title = 'Tweetonica';
            return;
        }
        var open = $('#groups a.gropen');
        var text = '';
        if (open.length) {
             text = open.eq(0).text() + " - Tweetonica";
        }
        var closed = $('#groups a .unread')
        for (var i = 0; i < closed.length; i++) {
            var current = closed.eq(i);
            if (current.data('count') != 0) {
                text = "***NEW*** " + text;
                break;
            };
        };
        document.title = text;
    }
    
    var show_mark_button = function() {
        if ($('.act').attr('id')!='mthreads') return;
        $('#markasread').css('position','absolute').animate(
         { left: $('#group-box').width()-150+$('#group-box').position().left,
           top: $('#group-box').position().top+1 }, 0).show();        
    }

    var format_date = function(s) {
        var d = new Date();
        d.setTime(s * 1000 - d.getTimezoneOffset() * 60);
        var now = new Date();
        var delta = Math.max(0, ((new Date()).getTime() - d.getTime()) / 1000);
        if (delta < 20)
            return 'less than 20 seconds ago';
        else if (delta >= 20 && delta <= 50)
            return 'half a minute ago';
        else if (delta > 50 && delta <= 60)
            return 'less then a minute ago';
        else if (delta > 60 && delta <= 48 * 60)
            return 'about ' + Math.ceil(delta / 60) + ' minutes ago';
        else if (delta > 48 * 60 && delta <= 90 * 60)
            return 'about a hour ago';
        else if (delta > 90 * 60 && delta < 23 * 3600 + 31 * 60)
            return Math.ceil(delta / 3600) + ' hours ago';
        else if (delta >= 23 * 3600 + 31 * 60 && delta < 30 * 24 * 3600)
            return Math.ceil(delta / (24 * 3600)) + ' days ago';
        return d.getMonth() + '/' + d.getDate() + '/' + d.getFullYear();
    }
    
    var update_dates = function() {
        $('.msg-header').each(function() {
            var header = $(this);
            var date = header.children('.msg-date').eq(0);
            var created = header.data('date');
            date.text(format_date(created));  
        });
    }

    var set_post_text = function(s) {
        if (s.length > 140)
            s = s.substring(0, 140);
        $('#message-text').val(s);
        $('#chars-left').text(140 - s.length);
    }

    var check_message = function() {
       var message = $('#message-text').val();
       if (message.length >= 140)
       {
           message = message.substring(0, 140);
           $('#message-text').val(message);
       }
       $('#chars-left').text(140 - message.length);
    }

    var direct_check_message = function() {
       var message = $('#direct-message-text').val();
       if (message.length >= 140)
       {
           message = message.substring(0, 140);
           $('#direct-message-text').val(message);
       }
       $('#direct-chars-left').text(140 - message.length);
    }

    var compose_feed = function(feed) {
        var container = $('<div class="usermsg" id="msg-' + feed.id + '">');
        if (!feed.reply) {
            container.append('<div class="userinfo_pic"><img src="' + feed.from.profile_image_url + '" alt="vzaliva" width="48" height="48"/></div>');
        }
        container.append('<a href="http://twitter.com/' + feed.from.screen_name + '" target="_blank"><span class="feed-author-name">' + feed.from.screen_name + '</span></a>');
        container.append($('<a href="http://twitter.com/' + feed.from.screen_name + '/status/' + feed.id + '" target="_blank" class="msg-header"><span class="msg-date">' + format_date(feed.created_at) + '</span></a><br/>').data('date', feed.created_at));
        container.append('<span class="feed-text">' + feed.html + '</span>');

        var buttons = $('<div class="msg-edit-buttons" id="btn-' + feed.id + '">');
        var btn_direct = $('<a href="javascript:;">').click(function(e) {
            var id = $(this).parent().attr('id').substring(4);
            $('#direct-message-text').val('');
            $('#direct-chars-left').text(140);
            var to = $('#msg-' + id + ' .feed-author-name').text();
            $('.direct-msg label span').text(to);
            $('#target-user').val(to);
            $('#direct-post-dialog').dialog('open');
            e.stopPropagation();
            e.preventDefault();
        });
        btn_direct.append('<img src="/images/direct_msg.png" alt="Direct Message"/>');
        buttons.append(btn_direct);

        var btn_reply = $('<a href="javascript:;">').click(function(e) {
            var id = $(this).parent().attr('id').substring(4);
            set_post_text('@' + $('#msg-' + id + ' .feed-author-name').text());
            $('#reply-to-status-id').val(id);
            $('#post-dialog').dialog('option', 'title', 'Reply').dialog('open');
            e.stopPropagation();
            e.preventDefault();
        });
        btn_reply.append('<img src="/images/reply.png" alt="Reply"/>');
        buttons.append(btn_reply);

        var btn_retweet = $('<a href="javascript:;">').click(function(e) {
            var id = $(this).parent().attr('id').substring(4);
            tweetonica.api.get_feed_by_id(id, function(result) {
                set_post_text('RT @' + result.from.screen_name + ' ' + result.text);
                $('#post-dialog').dialog('option', 'title', 'reTweet').dialog('open');
            }, function(error) {
                $('#error-description').text('Sorry, we were unable to retrieve feed data, please try again later');
                $('#error-dialog').dialog('open');
            });
            e.stopPropagation();
            e.preventDefault();
        });
        btn_retweet.append('<img src="/images/retweet.png" alt="reTweet"/>');
        buttons.append(btn_retweet);
        $('.feed-text a', container).attr('target', '_blank');
        return [container, buttons];
    }

    var load_feed = function(g, offset) {
        $('#feed_anchor').show();
        $('#btn-morefeed').hide();
        tweetonica.api.get_feed(g, offset, function(feed) {

            $('#groups a').each(function() {
                var o = $(this);
                if (o.data('groupname') == g.name) {
                    set_group_unread(o, 0);
                }
            });

            for (var i = 0; i < feed.length; i++) {
                var items = compose_feed(feed[i]);
                var container = items[0];
                var buttons = items[1];
                
                var anc = $('#feed_anchor');
                anc.before(container);
                anc.before(buttons);
                anc.before('<div class="line"></div>');

            }
            $('#feed_anchor').hide();
            $('#btn-morefeed').show().unbind('click').click(function(e) {
                load_feed(g, $('.usermsg').size());
                e.stopPropagation();
                e.preventDefault();
            });

        show_mark_button();

        }, function(error) {
            $('#feed_anchor').hide();
            $('#btn-morefeed').show().unbind('click').click(function(e) {
                load_feed(g, $('.usermsg').size());
                e.stopPropagation();
                e.preventDefault();
            });
        });
    }

    var update_feed = function(g, id, callback) {
        $('#feed_anchor').show();
        $('#btn-morefeed').hide();
        tweetonica.api.get_new_tweets(g, id, function(feed) {
            for (var i = 0; i < feed.length; i++) {
                var items = compose_feed(feed[i]);
                var container = items[0];
                var buttons = items[1];
                
                var anc = $(".usermsg").eq(0);
                var splitter = $('<div>').addClass("line");
                container.hide();
                buttons.hide();
                splitter.hide();
                anc.before(container);
                anc.before(buttons);
                anc.before(splitter);
                container.slideDown('slow');
                buttons.slideDown('slow');
                splitter.slideDown('slow');

            }
            $('#feed_anchor').hide();
            $('#btn-morefeed').show().unbind('click').click(function(e) {
                load_feed(g, $('.usermsg').size());
                e.stopPropagation();
                e.preventDefault();
            });

            if (callback) { callback(); }

        }, function(error) {
            $('#feed_anchor').hide();
            $('#btn-morefeed').show().unbind('click').click(function(e) {
                load_feed(g, $('.usermsg').size());
                e.stopPropagation();
                e.preventDefault();
            });
        });
    };
    
    var silent_refresh = function() {
        var opengr = cache[$('#groups .gropen').data('groupname')];
        if (opengr) {
            if ($('.usermsg').length) {
                lastid = $('.usermsg').attr('id').split('-')[1];
                update_feed(opengr.name, lastid, refresh_unread_count);
            }
            else {
                update_feed(opengr.name, 0, refresh_unread_count);
            }
            update_title();
            update_dates();
        };
    }
    
    var mark_group_read = function(g) {
        $('#feed_anchor').show();
        $('#btn-morefeed').hide();
        
        set_group_unread($('#groups .gropen'), 0);
        var messages = $('.usermsg')
        if (messages.length == 0) {
            set_group_unread(g, 0);
            $('#feed_anchor').hide();
            $('#btn-morefeed').show().unbind('click').click(function(e) {
                load_feed(g, $('.usermsg').size());
                e.stopPropagation();
                e.preventDefault();
            });
            return;
        }
        var lastid = messages.attr('id').split('-')[1];
        
        tweetonica.api.mark_group_read(g.data('groupname'), lastid, function(success) {
            set_group_unread(g, 0);
            $('#feed_anchor').hide();
            $('#btn-morefeed').show().unbind('click').click(function(e) {
                load_feed(g, $('.usermsg').size());
                e.stopPropagation();
                e.preventDefault();
            });
            update_title();
            
        }, function(error) {
            $('#feed_anchor').hide();
            $('#btn-morefeed').show().unbind('click').click(function(e) {
                load_feed(g, $('.usermsg').size());
                e.stopPropagation();
                e.preventDefault();
            });
        });
    }
	
    var render_group = function(g) {

        var container = $('<div class="group-background groupentry">')
        if (g.name != '__REPLIES__')
        {
            container.droppable({
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
        }

        var c = COLORS[COLOR++];
        if (COLOR >= COLORS.length)
            COLOR = 0;
        var node = $('<a href="javascript:;" ' + (g.name != '__ALL__' ? '' : ' id="root"') + ' class="grclosed ' + c + '-sm color-' + c + '"></a>').attr({
        }).data('groupname', g.name).click(function(e) {
            open_group($(this));
            e.stopPropagation();
            e.preventDefault();
        });

        var span = $('<span class="groupname">').text(display_group_name(g.name, true));
        var span2 = $('<span>');//.text(display_unread(g.unread));
        span2.addClass('unread');
        span2.data('groupname', g.name)
        node.append(span).append(span2);

        set_group_unread(node, g.unread);
        container.append(node.append(span).append(span2));


        if (g.name != '__ALL__' && g.name != '__REPLIES__') {
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
        
        if (g.name == '__REPLIES__') {
            container.addClass('repliesbox');
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

        var linkbox = '<div class="userinfo_screenname"><a href="http://twitter.com/' + u.screen_name + '" target="_blank">' + u.screen_name + '</a></div>';

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
        $('#groupmembers_members').append(container);
    }

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
            refresh_unread_count();
        }}, function(error) {
            $('#error-description').text('Sorry, we were unable to move your contact. Please try again later');
            $('#error-dialog').dialog('open');
        });
    };

    var delete_group = function(name) {
        $('#group-to-delete').val(name);
        $('#group-to-delete-name').text(name);
        $('#delete-confirm-dialog').dialog('open');
    }

    var create_group = function(name) {
        tweetonica.api.new_group(name, function(results) {
            var g = {name: name, users: [], rssurl: results.rssurl, unread: 0};
            cache[name] = g;
            render_group(g);
            open_group($('#groups a.gropen'));
            check_for_updates();
        }, function(error) {
            $('#error-description').text('Sorry, we were unable to create new group. Please try again later');
            $('#error-dialog').dialog('open');
        });
    }

    var reset_prefs = function() {
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
        }, function(error) {
            $('#error-description').text('Sorry, we were unable to rename group. Please try again later');
            $('#error-dialog').dialog('open');
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

        cache[e.data('groupname')].unread = 0;
        var g = cache[e.data('groupname')];
        $('#info_groupname').text(display_group_name(g.name));
        $('#info_groupfeed').attr('href', g.rssurl);
        $('#info_groupfeed_text').val(g.rssurl);

        $('#groupmembers_members').empty();
        $('#groupmembers_feed .usermsg, #groupmembers_feed .line, #groupmembers_feed .msg-edit-buttons').remove();
        for (var i = 0; i< g.users.length; i++) {
            render_user(g.users[i], g);
        }

        if ($('#groupmembers_feed').css('display') != 'none') {
            load_feed(g.name, 0);
        }
        
        set_group_unread(e, 0);
        $.cookie('last_group', g.name, { expires: 365, path: '/'});
            
        update_title();
    }

    var sync_groups = function(force, callback) {
         tweetonica.api.sync_friends(force, function(results) {
            if (callback)
                callback(results);
        }, function(error) {
            tweetonica.api.token = null;
            $.cookie('t.uname', null, {expires: -1, path: '/'});
            $.cookie('oauth.twitter', null, {expires: -1, path: '/'});
            $('.prefsmenu').hide();
            $('#currentuser').html('');
            $('#currentuserurl').attr('href', 'javascript:;');
            $('#loggedin').hide();
            $('#loggedout').show();
            open_page('error');
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

    var open_page = function(id) {
        if (id != 'manage' && id != 'prefs' && id != 'threads' || tweetonica.api.token) {
            if (id != 'threads') {
                $('#markasread').hide();
                $('.repliesbox').hide();
            }
            else {
                $('.repliesbox').show();
            }
            //else $('#markasread').show();
            $('.menu').removeClass('act');
            if (id == 'progress')
                $('#mmanage').addClass('act');
            else
                $('#m' + id).addClass('act');
            $('.page').hide();
            var p = $('#' + (id == 'threads' ? 'manage' : id));
            if (id != 'manage' && id != 'progress' && id != 'prefs' && id != 'threads')
               p.load(id + '.html div.' + id);
            p.show();

            if (id == 'threads') {
                $('.unread').show();
                $('#groupmembers_feed').show();
                $('#groupmembers_members').hide();
                $('.add-group').hide();
                $('.post-tweet').show();
                $('.tip').hide();
                $('.group-button a').hide();
                $('#group-box').addClass('purple');
                $('#view-style').hide();
                load_feed($('#groups a.gropen').data('groupname'), 0);
            } else if (id == 'manage') {
                $('.unread').hide();
                $('#groupmembers_feed').hide();
                $('#groupmembers_members').show();
                $('.add-group').show();
                $('.post-tweet').hide();
                $('.tip').show();
                $('.group-button a').show();
                $('#view-style').show();
                $('#group-box').removeClass('purple');
            }
            update_title();
        }
        else {
            document.location.href = '/oauth/login';
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
                $.cookie('t.uname', results.screen_name);
            }
            $('#opml_link').attr('href', results.OPML_download_url);
            $('#opml_text').val(results.OPML_feed_url);

            try {
                var outline   = document.createElement('link');
                outline.rel   = 'outline';
                outline.type  = 'text/x-opml';
                outline.title = 'OPML';
                outline.href = results.OPML_download_url;
                document.getElementsByTagName('head')[0].appendChild(outline);
            } catch (e) {}


            $('.prefsmenu').show();
            
            

            sync_groups(true, function(state) {
                refresh_groups(function() {
                    var tab = $.cookie('tt.tab');
                    open_page(tab == 'prefs' ? 'prefs' : (tab == 'manage' ? 'manage' : 'threads'));
                    $.cookie('tt.tab', null);
                });
            });
            
            
        }, function(error) {
            tweetonica.api.token = null;
            $.cookie('t.uname', null, {expires: -1, path: '/'});
            $.cookie('oauth.twitter', null, {expires: -1, path: '/'});
            $('.prefsmenu').hide();
            $('#currentuser').html('');
            $('#currentuserurl').attr('href', 'javascript:;');
            $('#loggedin').hide();
            $('#loggedout').show();
            open_page('error');
        });

        (function(fn, interval) {
            id = setInterval(function() {
                fn();
            }, interval);
        })(silent_refresh, 5*60000); // auto refresh every 5 minutes
        //})(silent_refresh, 20000); // auto refresh every 20 seconds (for debug)
        
        
        var btn = $('<a id="markasread" href="javascript:;"><img src="images/mark-button.png" alt="Mark all as read"></a>')
        .click(function() {
            mark_group_read($('#groups .gropen'));
            update_title(); 
        });
        btn.hide();
        $('.group-header')
        /*.append($('<a id="btn-reset-prefs" class="white" href="javascript:;">' +
        '<b class="utop"><b class="ub1"><b class="ub2"><b class="ub3"><b class="ub4">' +
        '<span class="prefs-box-content">Mark all as read</span>' +
        '<b class="ubottom"><b class="ub4"><b class="ub3"><b class="ub2"><b class="ub1">' + 
        '</a>')*/
        //.append($('<input type=button value="Mark all as read">')
        .append(btn);//.hide();
    };

    var refresh_unread_count = function() {
        tweetonica.api.get_friends(function(results) {
            var unread = {};
            for (var key in results) {
                var g = results[key];
                unread[g.name] = g.unread;
            }
            $('#groups a.gropen, a.grclosed').each(function() {
                var group = $(this);
                var grname = group.data('groupname');
                set_group_unread(group, unread[grname]);
            });
            var curunread = $('#groups .gropen .unread').data('count');
            update_title();
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
                if (a.name == '__REPLIES__') {
                    if (b.name == '__ALL__') return 1;
                    else return -1;
                }
                if (b.name == '__REPLIES__') {
                    if (a.name == '__ALL__') return -1;
                    else return 1;
                }
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
            
            
            if (!follows_tweetonica)
            {
                $('#followme').click(function(e) {
                    tweetonica.api.create_friendship('tweetonica', function(results) {
                        cache['__ALL__'].users.push({screen_name: 'tweetonica', real_name: 'tweetonica', profile_image_url: '/images/twitter-logo.png'});
                        open_group($('#groups a#root'));
                        $('#followme').unbind('click');
                        check_for_updates();
                    }, function(error) {
                        $('#error-description').text('Sorry, an error occured. Please try again later');
                        $('#error-dialog').dialog('open');
                    });
                    e.stopPropagation();
                    e.preventDefault();
                });
            }


            jgroups = $('#groups a.grclosed');
            lastgr = $.cookie('last_group');
            var opened = false;
            if (lastgr) {
                $('#groups a.grclosed').each(function() {
                    current = $(this);
                    if (current.data('groupname') == lastgr) {
                        open_group(current);
                        opened = true;
                    }
                });
            }
            if (!opened) {
                open_group($('#groups a#root'));
            }
            

            if (callback)
               callback();

        }, function(error) {
            $.cookie('t.uname', null, {expires: -1, path: '/'});
            $.cookie('oauth.twitter', null, {expires: -1, path: '/'});
            $('.prefsmenu').hide();
            $('#currentuser').html('');
            $('#currentuserurl').attr('href', 'javascript:;');
            $('#loggedin').hide();
            $('#loggedout').show();
            tweetonica.api.token = null;
            open_page('error');
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
                }, function(error) {
                    $('#error-description').text('Sorry, we were unable to delete group. Please try again later');
                    $('#error-dialog').dialog('open');
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

    $('#error-dialog').dialog({
        buttons: {
            'OK': function() {
                $('#error-dialog').dialog('close');
            }
        },
        autoOpen: false,
        modal: true,
        resizable: false,
        title: 'Error',
        width: 360,
        open: function() {
            $('object,embed').hide();
        },
        close: function() {
            $('object,embed').show();
        }
    });

    $('#post-dialog').dialog({
        buttons: {
            'Cancel': function() {
                $('#post-dialog').dialog('close');
            },
            'OK': function() {
                var text     = $('#message-text').val();
                var reply_to = $('#reply-to-status-id').val();
                tweetonica.api.post_tweet(text, reply_to, function(results) {
                    $('#post-dialog').dialog('close');
                }, function(error) {
                    $('#post-dialog').dialog('close');
                    $('#error-description').text('Sorry, we were unable to post your tweet. Please try again later');
                    $('#error-dialog').dialog('open');
                });
            }
        },
        autoOpen: false,
        modal: true,
        resizable: false,
        width: 300,
        open: function() {
            $('object,embed').hide();
            setTimeout(function() {$('#message-text').focus()}, 100);
        },
        close: function() {
            $('object,embed').show();
        }
    });

    $('#direct-post-dialog').dialog({
        buttons: {
            'Cancel': function() {
                $('#direct-post-dialog').dialog('close');
            },
            'OK': function() {
                var text = $('#direct-message-text').val();
                var to   = $('#target-user').val();
                tweetonica.api.post_direct_tweet(to, text, function(results) {
                    $('#direct-post-dialog').dialog('close');
                }, function(error) {
                    $('#direct-post-dialog').dialog('close');
                    $('#error-description').text('Sorry, we were unable to post your tweet. Please try again later');
                    $('#error-dialog').dialog('open');
                });
            }
        },
        autoOpen: false,
        modal: true,
        resizable: false,
        width: 300,
        title: 'Direct Message',
        open: function() {
            $('object,embed').hide();
            setTimeout(function() {$('#direct-message-text').focus()}, 100);
        },
        close: function() {
            $('object,embed').show();
        }
    });

    // handlers

    $('.menu').click(function(e) {
        if (this.id) {
            var pageid = this.id.substring(1);
            open_page(pageid);
            e.stopPropagation();
            e.preventDefault();
        }
    });

    $('.menulink').click(function(e) {
        if (this.id) {
            var pageid = this.id.substring(2);
            $('#m' + pageid).click();
            e.stopPropagation();
            e.preventDefault();
        }
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

        var temp_prefs = {};
        temp_prefs['remember_me']   = PREFS['remember_me'];
        temp_prefs['use_HTTP_auth'] = PREFS['use_HTTP_auth'];
        temp_prefs['icons_only'] = $('#vs-icons').attr('checked') ? true : false;

        tweetonica.api.set_prefs(temp_prefs, function(results) {
            PREFS = results;
        }, function(error) {
            $('#error-description').text('Sorry, we were unable to save your preferences. Please try again later');
            $('#error-dialog').dialog('open');
        });
    });

    $('.add-group a').click(function(e) {
        $('#create-group-name').val('');
        $('#create-dialog').dialog('open');
        e.stopPropagation();
        e.preventDefault();
    });

    var show_tooltip = function(e, o) {
        if (!$('#vs-icons').attr('checked'))
            return;
        $('#tt-screen').text($('.userinfo_screenname a', o.parent()).text());
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
        temp_prefs['icons_only'] = $(':radio[name=vs]:checked').val() == '1' ? true : false;

        tweetonica.api.set_prefs(temp_prefs, function(results) {
            PREFS = results;
            $('#opml_link').attr('href', results.OPML_download_url);
            $('#opml_text').val(results.OPML_feed_url);
            open_page('progress');
            refresh_groups(function() {
                open_page('prefs');
            });
        }, function(error) {
            $('#error-description').text('Sorry, we were unable to save your preferences. Please try again later');
            $('#error-dialog').dialog('open');
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

    $('#contactus').live('click', function() {
        open_page('contact');
    });

    $('#btn-morefeed').mouseover(function() {
        $('.lt-purple, .dk-purple').toggleClass('lt-purple').toggleClass('dk-purple');
        $('.more-box-content', $(this)).css('background', '#f3e1ff url(/css/images/bt-line-reverse.png) repeat-x');
    }).mouseout(function() {
        $('.lt-purple, .dk-purple').toggleClass('lt-purple').toggleClass('dk-purple');
        $('.more-box-content', $(this)).css('background', null);
    });

    $('.post-tweet').click(function(e) {
        set_post_text('');
        $('#reply-to-status-id').val('');
        $('#post-dialog').dialog('option', 'title', 'New Tweet').dialog('open');
        e.stopPropagation();
        e.preventDefault();
    });


    $('#message-text').keyup(check_message).keydown(check_message).change(check_message);
    $('#direct-message-text').keyup(direct_check_message).keydown(direct_check_message).change(direct_check_message);

    if (!$('#staticpage').length) {
        var cookie = $.cookie('oauth.twitter');
        if (cookie) {
            tweetonica.api.token = cookie;
            initialize(true);
        }
        else
            open_page('about');
    } else {
        var user = $.cookie('t.uname');
        if (user) {
            $('#currentuser').text(user);
            $('#currentuserurl').attr('href', 'http://twitter.com/' + user);
            $('#loggedin').show();
            $('#loggedout').hide();
            $('.prefsmenu').show().click(function(e) {
                $.cookie('tt.tab', 'prefs');
                document.location.href = '/';
                e.stopPropagation();
                e.preventDefault();
            });
            $('.manage').click(function(e) {
                $.cookie('tt.tab', 'manage');
                document.location.href = '/';
                e.stopPropagation();
                e.preventDefault();
            });
        }
    }

});
