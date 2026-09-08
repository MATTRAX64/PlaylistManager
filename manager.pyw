#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Playlist Manager — recherche / écoute / téléchargement de playlists YouTube.
Dépendances : pip install yt-dlp pywebview mutagen pygame   |  Externe : ffmpeg dans le PATH.
Lancement   : double-clic (Windows) ou `python music_manager.pyw`
"""
import json, os, sys, shutil, tempfile, traceback, threading, urllib.parse
from datetime import datetime
from pathlib import Path

APP_DIR = Path(__file__).resolve().parent
DATA_FILE = APP_DIR / "data.json"
SETTINGS_FILE = APP_DIR / "settings.json"
DEFAULT_DL_DIR = APP_DIR / "Playlists"
TEMP_DIR = Path(tempfile.gettempdir()) / "playlist_manager_temp"
TEMP_DIR.mkdir(exist_ok=True)
# NB: DEFAULT_DL_DIR n'est PAS créé ici — il ne doit apparaître qu'au moment d'un
# vrai téléchargement (voir YT.download_permanent), pas juste au lancement de l'app.

INDEX_HTML = """<!DOCTYPE html>
<html lang="fr"><head><meta charset="UTF-8"><title>Playlist Manager</title>
<style>
:root{--bg-void:#000;--bg-base:#0a0a0a;--bg-elev:#121212;--bg-card:#181818;--bg-card-h:#232323;--bg-hl:#2a2a2a;
--accent:#1ed760;--accent-h:#3ee879;--text:#fff;--text2:#a7a7a7;--text3:#6a6a6a;
--danger:#f15e6c;--warning:#e8a33d;--r-sm:4px;--r-md:8px;--r-lg:12px;--r-full:999px;
--sidebar-w:260px;--player-h:88px;--topbar-h:64px;--font:"Segoe UI",Inter,-apple-system,sans-serif}
*{box-sizing:border-box;margin:0;padding:0}
html,body{height:100%;overflow:hidden;background:var(--bg-void);color:var(--text);font-family:var(--font);user-select:none}
::-webkit-scrollbar{width:12px}::-webkit-scrollbar-thumb{background:rgba(255,255,255,.15);border-radius:6px;border:3px solid var(--bg-void)}
button{font-family:inherit;cursor:pointer;border:none;background:none;color:inherit}input{font-family:inherit}
#app{display:grid;grid-template-columns:var(--sidebar-w) 1fr;grid-template-rows:1fr var(--player-h);height:100vh;gap:8px;padding:8px}
#sidebar{background:var(--bg-base);border-radius:var(--r-lg);display:flex;flex-direction:column;padding:20px 12px;overflow:hidden}
.brand{display:flex;align-items:center;gap:10px;padding:0 12px 24px}
.brand-logo{width:32px;height:32px;border-radius:50%;background:var(--accent);display:flex;align-items:center;justify-content:center;font-size:18px}
.brand-name{font-size:20px;font-weight:800}
.nav-item{display:flex;align-items:center;gap:14px;padding:10px 12px;border-radius:var(--r-sm);color:var(--text2);font-size:14.5px;font-weight:600;margin-bottom:22px}
.nav-item svg{width:20px;height:20px}.nav-item.active{color:var(--text)}.nav-item.active svg{color:var(--accent)}
.sidebar-divider{height:1px;background:rgba(255,255,255,.08);margin:4px 12px 16px}
.fav-header{display:flex;align-items:center;justify-content:space-between;padding:0 12px 10px}
.fav-title{font-size:12.5px;font-weight:700;color:var(--text2);text-transform:uppercase;letter-spacing:.04em}
.icon-btn{width:28px;height:28px;border-radius:50%;display:flex;align-items:center;justify-content:center;color:var(--text2)}
.icon-btn:hover{background:var(--bg-hl);color:var(--text)}.icon-btn svg{width:16px;height:16px}
#fav-list{flex:1;overflow-y:auto;display:flex;flex-direction:column;gap:1px}
.fav-item{display:flex;align-items:center;gap:12px;padding:8px 12px;border-radius:var(--r-sm);cursor:pointer}
.fav-item:hover,.fav-item.selected{background:var(--bg-hl)}
.fav-cover{width:40px;height:40px;border-radius:var(--r-sm);background:linear-gradient(135deg,#333,#1a1a1a);display:flex;align-items:center;justify-content:center;font-size:16px;flex-shrink:0}
.fav-info{flex:1;min-width:0}.fav-name{font-size:13.5px;font-weight:600;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.fav-sub{font-size:12px;color:var(--text3);white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.fav-item.deleted .fav-name,.fav-item.deleted .fav-sub{color:var(--danger)}
.status-dot{width:7px;height:7px;border-radius:50%;background:var(--accent);flex-shrink:0}
.fav-item.deleted .status-dot{background:var(--danger)}
.empty-fav{padding:20px 12px;color:var(--text3);font-size:13px;line-height:1.5}
#main{background:linear-gradient(180deg,#1a1a1a 0,var(--bg-elev) 320px);border-radius:var(--r-lg);display:flex;flex-direction:column;overflow:hidden}
#topbar{height:var(--topbar-h);display:flex;align-items:center;justify-content:space-between;padding:0 24px;flex-shrink:0}
.nav-arrows button{width:32px;height:32px;border-radius:50%;background:rgba(0,0,0,.4);display:flex;align-items:center;justify-content:center}
.nav-arrows svg{width:18px;height:18px}
#search-box{flex:1;max-width:420px;margin:0 20px;position:relative}
#search-input{width:100%;background:var(--bg-card);border:1px solid transparent;border-radius:var(--r-full);padding:10px 16px 10px 42px;color:var(--text);font-size:14px}
#search-input:focus{outline:none;background:#202020;border-color:var(--text3)}
#search-box svg{position:absolute;left:14px;top:50%;transform:translateY(-50%);width:16px;height:16px;color:var(--text2);pointer-events:none}
.settings-btn{width:34px;height:34px;border-radius:50%;background:var(--bg-card);display:flex;align-items:center;justify-content:center;color:var(--text2)}
.settings-btn:hover{color:var(--text)}.settings-btn.spinning svg{animation:spin .6s ease}
@keyframes spin{to{transform:rotate(180deg)}}.settings-btn svg{width:18px;height:18px}
#content{flex:1;overflow-y:auto;padding:8px 24px 24px}
.view{display:none}.view.active{display:block;animation:fadein .2s ease}
@keyframes fadein{from{opacity:0;transform:translateY(6px)}to{opacity:1;transform:none}}
.view-header{margin:16px 0 20px}.view-title{font-size:26px;font-weight:800}
.view-sub{color:var(--text2);font-size:13.5px;margin-top:4px}
.card-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(170px,1fr));gap:20px}
.pl-card{background:var(--bg-card);border-radius:var(--r-md);padding:14px;position:relative;cursor:pointer}
.pl-card:hover{background:var(--bg-card-h)}
.pl-cover{width:100%;aspect-ratio:1;border-radius:var(--r-sm);background:linear-gradient(135deg,#3a3a3a,#161616);display:flex;align-items:center;justify-content:center;font-size:36px;margin-bottom:14px;position:relative;overflow:hidden}
.pl-play-fab{position:absolute;right:22px;bottom:74px;width:44px;height:44px;border-radius:50%;background:var(--accent);color:#000;display:flex;align-items:center;justify-content:center;opacity:0;transform:translateY(6px)}
.pl-card:hover .pl-play-fab{opacity:1;transform:none}.pl-play-fab:hover{background:var(--accent-h)}
.pl-play-fab svg{width:18px;height:18px;margin-left:2px}
.pl-name{font-size:14.5px;font-weight:700;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;margin-bottom:4px}
.pl-channel{font-size:12.5px;color:var(--text2);white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.pl-meta-line{font-size:11.5px;color:var(--text3);white-space:nowrap;overflow:hidden;text-overflow:ellipsis;margin-top:2px}
.pl-star-btn{position:absolute;top:10px;right:10px;width:30px;height:30px;border-radius:50%;background:rgba(0,0,0,.55);display:flex;align-items:center;justify-content:center;color:#fff;opacity:0}
.pl-card:hover .pl-star-btn{opacity:1}.pl-star-btn:hover{color:var(--accent)}.pl-star-btn.saved{opacity:1;color:var(--accent)}
.pl-star-btn svg{width:15px;height:15px}
.pl-detail-header{display:flex;align-items:flex-end;gap:24px;padding:24px 0 28px}
.pl-detail-cover{width:192px;height:192px;border-radius:var(--r-md);background:linear-gradient(135deg,#444,#161616);display:flex;align-items:center;justify-content:center;font-size:64px;flex-shrink:0}
.pl-detail-meta{display:flex;flex-direction:column;gap:10px}
.pl-detail-type{font-size:12px;font-weight:700;text-transform:uppercase;color:var(--accent)}
.pl-detail-title{font-size:38px;font-weight:900;line-height:1.1}
.pl-detail-sub{font-size:13.5px;color:var(--text2);display:flex;align-items:center;gap:6px}
.status-badge{font-size:11.5px;font-weight:700;padding:3px 9px;border-radius:var(--r-full);text-transform:uppercase}
.status-badge.deleted{background:rgba(241,94,108,.15);color:var(--danger)}
.pl-detail-actions{display:flex;align-items:center;gap:18px;padding:4px 0 20px;flex-wrap:wrap}
.play-all-btn{width:56px;height:56px;border-radius:50%;background:var(--accent);color:#000;display:flex;align-items:center;justify-content:center}
.play-all-btn:hover{background:var(--accent-h)}.play-all-btn svg{width:24px;height:24px;margin-left:3px}
.dl-all-btn,.remove-fav-btn,.recheck-btn{display:flex;align-items:center;gap:8px;padding:9px 16px;border-radius:var(--r-full);border:1px solid rgba(255,255,255,.25);font-size:13.5px;font-weight:700}
.dl-all-btn:hover,.recheck-btn:hover{border-color:#fff}
.remove-fav-btn{border-color:rgba(241,94,108,.4);color:var(--danger)}.remove-fav-btn:hover{border-color:var(--danger)}
.dl-all-btn svg,.remove-fav-btn svg,.recheck-btn svg{width:15px;height:15px}
.track-table{display:flex;flex-direction:column}
.track-row{display:grid;grid-template-columns:32px 1fr 150px 90px 90px;align-items:center;gap:14px;padding:8px 12px;border-radius:var(--r-sm)}
.track-row:hover{background:rgba(255,255,255,.06)}
.track-row.header-row{color:var(--text3);font-size:12px;text-transform:uppercase;border-bottom:1px solid rgba(255,255,255,.08);margin-bottom:6px;padding-bottom:10px}
.track-row.header-row:hover{background:none}
.track-num{color:var(--text3);font-size:14px;text-align:center}.track-row:hover .track-num{display:none}
.track-play-icon{display:none;width:14px;height:14px;margin:0 auto;color:#fff}.track-row:hover .track-play-icon{display:block}
.track-title-cell{min-width:0;display:flex;flex-direction:column;gap:2px}
.track-title{font-size:14.5px;font-weight:600;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.track-row.blocked .track-title{color:var(--warning)}.track-row.playing .track-title{color:var(--accent)}
.track-reason{font-size:11.5px;color:var(--warning);white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.track-duration{color:var(--text2);font-size:13px;text-align:right}
.track-meta-line{font-size:12px;color:var(--text3);white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.track-row.blocked .track-meta-line{display:none}
.track-actions{display:flex;gap:6px;justify-content:flex-end}
.track-actions button{width:28px;height:28px;border-radius:50%;display:flex;align-items:center;justify-content:center;color:var(--text2);opacity:0}
.track-row:hover .track-actions button{opacity:1}
.track-actions button:hover{color:var(--text);background:var(--bg-hl)}
.track-actions button.downloaded{color:var(--accent);opacity:1}
.track-actions button svg{width:15px;height:15px}.track-actions button:disabled{opacity:.25!important;cursor:not-allowed}
.empty-state{display:flex;flex-direction:column;align-items:center;justify-content:center;padding:80px 20px;color:var(--text3);text-align:center;gap:12px}
.empty-state svg{width:48px;height:48px;opacity:.5}
.empty-state-title{font-size:16px;font-weight:700;color:var(--text2)}
.empty-state-sub{font-size:13.5px;max-width:320px;line-height:1.5}
#player-bar{grid-column:1/3;background:var(--bg-base);border-radius:var(--r-lg);display:grid;grid-template-columns:1fr 1.4fr 1fr;align-items:center;padding:0 16px;gap:12px;position:relative}
.now-playing{display:flex;align-items:center;gap:12px;min-width:0}
.np-cover{width:56px;height:56px;border-radius:var(--r-sm);background:linear-gradient(135deg,#3a3a3a,#161616);display:flex;align-items:center;justify-content:center;font-size:20px;flex-shrink:0}
.np-info{min-width:0}.np-title{font-size:13.5px;font-weight:600;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.np-sub{font-size:11.5px;color:var(--text2)}.np-empty{color:var(--text3);font-size:13px}
.player-center{display:flex;flex-direction:column;align-items:center;gap:8px}
.transport{display:flex;align-items:center;gap:18px}.transport button{color:var(--text2)}.transport button:hover{color:var(--text)}
#play-pause-btn{width:34px;height:34px;border-radius:50%;background:#fff;color:#000;display:flex;align-items:center;justify-content:center}
#play-pause-btn svg{width:16px;height:16px}.transport svg{width:17px;height:17px}
.progress-row{display:flex;align-items:center;gap:8px;width:100%;max-width:480px}
.time-label{font-size:11px;color:var(--text3);width:34px;text-align:center;flex-shrink:0}
.progress-track,.volume-track{height:4px;background:rgba(255,255,255,.18);border-radius:var(--r-full);position:relative;cursor:pointer}
.progress-track{flex:1}
.progress-fill,.volume-fill{position:absolute;left:0;top:0;height:100%;background:var(--text);border-radius:var(--r-full);pointer-events:none}
.progress-track:hover .progress-fill,.volume-track:hover .volume-fill{background:var(--accent)}
.player-right{display:flex;align-items:center;justify-content:flex-end;gap:14px}
.player-right button{color:var(--text2)}.player-right button:hover{color:var(--text)}.player-right svg{width:16px;height:16px}
.volume-row{display:flex;align-items:center;gap:8px;width:110px}
.volume-row .volume-track{flex:1;min-width:0}
.player-status-toast{position:absolute;left:50%;transform:translateX(-50%);top:-34px;font-size:12px;color:var(--text2);background:var(--bg-elev);padding:5px 12px;border-radius:var(--r-full);white-space:nowrap;opacity:0;transition:opacity .2s;display:flex;align-items:center;gap:8px}
.player-status-toast.show{opacity:1}
.player-status-toast .pst-bar{width:70px;height:4px;border-radius:var(--r-full);background:rgba(255,255,255,.15);overflow:hidden;flex-shrink:0}
.player-status-toast .pst-bar-fill{height:100%;width:0%;background:var(--accent);border-radius:var(--r-full);transition:width .15s linear}
.player-status-toast .pst-bar.hidden{display:none}
.modal-overlay{position:fixed;inset:0;background:rgba(0,0,0,.7);display:flex;align-items:center;justify-content:center;z-index:100;opacity:0;pointer-events:none;transition:opacity .15s}
.modal-overlay.show{opacity:1;pointer-events:all}
.modal-box{width:560px;max-height:82vh;background:var(--bg-elev);border-radius:var(--r-lg);display:flex;flex-direction:column;box-shadow:0 24px 64px rgba(0,0,0,.6)}
.modal-header{display:flex;align-items:center;justify-content:space-between;padding:20px 24px;border-bottom:1px solid rgba(255,255,255,.08)}
.modal-title{font-size:18px;font-weight:800}
.modal-close{width:30px;height:30px;border-radius:50%;display:flex;align-items:center;justify-content:center;color:var(--text2)}
.modal-close:hover{color:var(--text);background:var(--bg-hl)}.modal-close svg{width:16px;height:16px}
.modal-body{overflow-y:auto;padding:8px 24px 24px}
.setting-group{padding:18px 0;border-bottom:1px solid rgba(255,255,255,.06)}.setting-group:last-child{border-bottom:none}
.setting-group-title{font-size:15px;font-weight:700;margin-bottom:14px}
.setting-row{display:flex;align-items:center;justify-content:space-between;padding:10px 0;gap:20px}
.setting-label{font-size:14px;font-weight:600}.setting-desc{font-size:12px;color:var(--text3);margin-top:2px;word-break:break-all}
.toggle{width:44px;height:24px;border-radius:var(--r-full);background:var(--bg-hl);position:relative;flex-shrink:0;transition:background .2s}
.toggle::after{content:'';position:absolute;top:2px;left:2px;width:20px;height:20px;border-radius:50%;background:#fff;transition:transform .2s}
.toggle.on{background:var(--accent)}.toggle.on::after{transform:translateX(20px)}
.select-input{background:var(--bg-card);border:1px solid rgba(255,255,255,.12);border-radius:var(--r-sm);color:var(--text);padding:8px 12px;font-size:13.5px;min-width:160px}
.select-input:focus{outline:none;border-color:var(--accent)}
.accent-swatches{display:flex;gap:10px}
.swatch{width:26px;height:26px;border-radius:50%;border:2px solid transparent}
.swatch:hover{transform:scale(1.1)}.swatch.active{border-color:#fff}
.folder-row{display:flex;flex-direction:column;align-items:flex-end;gap:6px;max-width:280px}
.small-btn{padding:7px 14px;border-radius:var(--r-full);border:1px solid rgba(255,255,255,.2);font-size:12.5px;font-weight:700}
.small-btn:hover{border-color:#fff}
.danger-btn{color:var(--danger);border:1px solid rgba(241,94,108,.4)}
.danger-btn:hover{border-color:var(--danger);background:rgba(241,94,108,.08)}
.spinner{width:16px;height:16px;border:2px solid rgba(255,255,255,.25);border-top-color:#fff;border-radius:50%;animation:rotate .7s linear infinite}
@keyframes rotate{to{transform:rotate(360deg)}}
.loading-row{display:flex;align-items:center;gap:10px;color:var(--text2);padding:40px 0;justify-content:center}
.fetch-progress-wrap{display:flex;flex-direction:column;align-items:center;gap:14px;padding:60px 20px}
.fetch-progress-text{font-size:14px;color:var(--text2)}
.fetch-progress-bar{width:320px;height:6px;background:rgba(255,255,255,.12);border-radius:var(--r-full);overflow:hidden}
.fetch-progress-fill{height:100%;width:0%;background:var(--accent);border-radius:var(--r-full);transition:width .15s}
#toast{position:fixed;bottom:calc(var(--player-h) + 24px);left:50%;transform:translateX(-50%) translateY(10px);background:var(--bg-elev);border:1px solid rgba(255,255,255,.1);padding:12px 20px;border-radius:var(--r-md);font-size:13.5px;box-shadow:0 8px 24px rgba(0,0,0,.5);z-index:200;opacity:0;pointer-events:none;transition:opacity .2s,transform .2s;display:flex;align-items:center;gap:10px}
#toast.show{opacity:1;transform:translateX(-50%) translateY(0)}
#toast.warning{border-color:rgba(232,163,61,.4)}#toast.danger{border-color:rgba(241,94,108,.4)}
</style></head>
<body>
<div id="app">
  <aside id="sidebar">
    <div class="brand"><div class="brand-logo">🎧</div><div class="brand-name">Playlist</div></div>
    <nav><a class="nav-item active"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="7"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg><span data-i18n="navSearch">Rechercher</span></a></nav>
    <div class="sidebar-divider"></div>
    <div class="fav-header"><span class="fav-title" data-i18n="favTitle">Tes playlists</span>
      <button class="icon-btn" id="recheck-all-btn" title="Vérifier la disponibilité"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M23 4v6h-6"/><path d="M1 20v-6h6"/><path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15"/></svg></button>
    </div>
    <div id="fav-list"><div class="empty-fav" data-i18n="favEmpty">Aucune playlist sauvegardée. Cherche-en une et clique sur l'étoile ⭐.</div></div>
  </aside>
  <main id="main">
    <div id="topbar">
      <div class="nav-arrows"><button id="back-btn" title="Retour"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M15 18l-6-6 6-6"/></svg></button></div>
      <div id="search-box"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="7"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>
        <input type="text" id="search-input" data-i18n-placeholder="searchPlaceholder" placeholder="Cherche une playlist, ou colle un lien YouTube..."></div>
      <div><button class="settings-btn" id="settings-btn" data-i18n-title="settingsTitle" title="Paramètres"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 1 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 1 1-2.83-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 1 1 2.83-2.83l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 1 1 2.83 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z"/></svg></button></div>
    </div>
    <div id="content">
      <section class="view active" id="view-search">
        <div class="view-header"><div class="view-title" data-i18n="searchTitle">Rechercher des playlists</div>
          <div class="view-sub" data-i18n="searchSub">Colle un lien de playlist YouTube (le plus fiable), ou tape un mot-clé</div></div>
        <div id="search-results"><div class="empty-state"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><circle cx="11" cy="11" r="7"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>
          <div class="empty-state-title" data-i18n="emptyTitle">Trouve tes playlists</div><div class="empty-state-sub" data-i18n="emptySub">Colle un lien type youtube.com/playlist?list=... pour un résultat garanti, ou cherche par mot-clé.</div></div></div>
      </section>
      <section class="view" id="view-playlist"><div id="playlist-detail-content"></div></section>
    </div>
  </main>
  <div id="player-bar">
    <div class="player-status-toast" id="player-toast"><span id="player-toast-text"></span><div class="pst-bar hidden" id="player-toast-bar"><div class="pst-bar-fill" id="player-toast-bar-fill"></div></div></div>
    <div class="now-playing" id="now-playing"><div class="np-empty" data-i18n="noPlayback">Aucune lecture en cours</div></div>
    <div class="player-center">
      <div class="transport">
        <button id="prev-btn" data-i18n-title="prevTitle" title="Précédent"><svg viewBox="0 0 24 24" fill="currentColor"><path d="M6 6h2v12H6zm3.5 6l8.5 6V6z"/></svg></button>
        <button id="play-pause-btn" data-i18n-title="playPauseTitle" title="Lecture/Pause"><svg id="play-icon" viewBox="0 0 24 24" fill="currentColor"><path d="M8 5v14l11-7z"/></svg><svg id="pause-icon" viewBox="0 0 24 24" fill="currentColor" style="display:none"><path d="M6 5h4v14H6zM14 5h4v14h-4z"/></svg></button>
        <button id="next-btn" data-i18n-title="nextTitle" title="Suivant"><svg viewBox="0 0 24 24" fill="currentColor"><path d="M16 18h2V6h-2zM6 18l8.5-6L6 6z"/></svg></button>
      </div>
      <div class="progress-row"><span class="time-label" id="time-current">0:00</span>
        <div class="progress-track" id="progress-track"><div class="progress-fill" id="progress-fill"></div></div>
        <span class="time-label" id="time-total">0:00</span></div>
    </div>
    <div class="player-right">
      <button id="download-current-btn" data-i18n-title="downloadTrackTitle" title="Télécharger ce titre" disabled><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg></button>
      <div class="volume-row"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"/><path d="M15.54 8.46a5 5 0 0 1 0 7.07"/></svg>
        <div class="volume-track" id="volume-track"><div class="volume-fill" id="volume-fill"></div></div></div>
    </div>
  </div>
</div>
<div class="modal-overlay" id="settings-modal">
  <div class="modal-box">
    <div class="modal-header"><div class="modal-title" data-i18n="settingsTitle">Paramètres</div>
      <button class="modal-close" id="close-settings-btn"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg></button></div>
    <div class="modal-body">
      <div class="setting-group"><div class="setting-group-title" data-i18n="groupGeneral">Général</div>
        <div class="setting-row"><div><div class="setting-label" data-i18n="languageLabel">Langue</div><div class="setting-desc" data-i18n="languageDesc">Langue de l'interface</div></div>
          <select class="select-input" id="language-select">
            <option value="fr">Français</option>
            <option value="en">English</option>
            <option value="de">Deutsch</option>
            <option value="es">Español</option>
            <option value="ja">日本語</option>
            <option value="ru">Русский</option>
          </select></div>
      </div>
      <div class="setting-group"><div class="setting-group-title" data-i18n="groupAppearance">Apparence</div>
        <div class="setting-row"><div><div class="setting-label" data-i18n="accentLabel">Couleur d'accent</div><div class="setting-desc" data-i18n="accentDesc">Boutons et surlignages</div></div>
          <div class="accent-swatches" id="accent-swatches">
            <div class="swatch active" data-color="#1ed760" style="background:#1ed760"></div>
            <div class="swatch" data-color="#4a9eff" style="background:#4a9eff"></div>
            <div class="swatch" data-color="#f15e6c" style="background:#f15e6c"></div>
            <div class="swatch" data-color="#e8a33d" style="background:#e8a33d"></div>
            <div class="swatch" data-color="#c774e8" style="background:#c774e8"></div>
            <div class="swatch" data-color="#ffffff" style="background:#fff"></div>
          </div></div>
        <div class="setting-row"><div><div class="setting-label" data-i18n="densityLabel">Densité des cartes</div><div class="setting-desc" data-i18n="densityDesc">Taille des vignettes</div></div>
          <select class="select-input" id="density-select"><option value="compact" data-i18n="densityCompact">Compacte</option><option value="normal" selected data-i18n="densityNormal">Normale</option><option value="large" data-i18n="densityLarge">Grande</option></select></div>
      </div>
      <div class="setting-group"><div class="setting-group-title" data-i18n="groupPlayback">Lecture</div>
        <div class="setting-row"><div><div class="setting-label" data-i18n="qualityLabel">Qualité audio</div><div class="setting-desc" data-i18n="qualityDesc">Qualité du MP3</div></div>
          <select class="select-input" id="quality-select"><option value="128">128 kbps</option><option value="192" selected>192 kbps</option><option value="320">320 kbps</option></select></div>
        <div class="setting-row"><div><div class="setting-label" data-i18n="autoplayLabel">Lecture automatique</div><div class="setting-desc" data-i18n="autoplayDesc">Enchaîne le titre suivant</div></div><div class="toggle on" id="autoplay-toggle"></div></div>
        <div class="setting-row"><div><div class="setting-label" data-i18n="volumeLabel">Volume de départ</div><div class="setting-desc" data-i18n="volumeDesc">Volume au lancement</div></div>
          <select class="select-input" id="default-volume-select"><option value="0.5">50%</option><option value="0.8" selected>80%</option><option value="1.0">100%</option></select></div>
      </div>
      <div class="setting-group"><div class="setting-group-title" data-i18n="groupDownloads">Téléchargements</div>
        <div class="setting-row"><div><div class="setting-label" data-i18n="folderLabel">Dossier de téléchargement</div><div class="setting-desc" id="download-folder-path"> Playlists/</div></div>
          <div class="folder-row"><button class="small-btn" id="choose-folder-btn" data-i18n="changeBtn">Changer</button></div></div>
        <div class="setting-row"><div><div class="setting-label" data-i18n="organizeLabel">Ranger par playlist</div><div class="setting-desc" data-i18n="organizeDesc">Sous-dossier par playlist</div></div><div class="toggle on" id="organize-toggle"></div></div>
        <div class="setting-row"><div><div class="setting-label" data-i18n="revealLabel">Ouvrir le dossier après téléchargement</div><div class="setting-desc" data-i18n="revealDesc">Affiche le fichier une fois terminé</div></div><div class="toggle" id="reveal-toggle"></div></div>
      </div>
      <div class="setting-group"><div class="setting-group-title" data-i18n="groupData">Données</div>
        <div class="setting-row"><div><div class="setting-label" data-i18n="autocheckLabel">Vérification automatique</div><div class="setting-desc" data-i18n="autocheckDesc">Au démarrage</div></div><div class="toggle on" id="autocheck-toggle"></div></div>
        <div class="setting-row"><div><div class="setting-label" data-i18n="clearCacheLabel">Nettoyer le cache temporaire</div><div class="setting-desc" data-i18n="clearCacheDesc">Fichiers audio d'écoute</div></div><button class="small-btn" id="clear-cache-btn" data-i18n="cleanBtn">Nettoyer</button></div>
        <div class="setting-row"><div><div class="setting-label" data-i18n="resetLabel">Réinitialiser toutes les playlists</div><div class="setting-desc" data-i18n="resetDesc">Irréversible</div></div><button class="small-btn danger-btn" id="reset-data-btn" data-i18n="resetBtn">Tout supprimer</button></div>
      </div>
    </div>
  </div>
</div>
<div id="toast"></div>

<script>
const state = {
  favorites: {}, currentPlaylistId: null, queue: [], queueIndex: -1, isPlaying: false,
  settings: { accent:"#1ed760", density:"normal", quality:"192", autoplay:true, defaultVolume:0.8,
              organizeByPlaylist:true, revealAfterDownload:false, autocheck:true, downloadFolder:"Playlists/",
              language:"fr" }
};

/* ---------- Traduction de l'interface ---------- */
const I18N = {
  fr:{ settingsTitle:"Paramètres", groupGeneral:"Général", languageLabel:"Langue", languageDesc:"Langue de l'interface",
       groupAppearance:"Apparence", accentLabel:"Couleur d'accent", accentDesc:"Boutons et surlignages",
       densityLabel:"Densité des cartes", densityDesc:"Taille des vignettes",
       densityCompact:"Compacte", densityNormal:"Normale", densityLarge:"Grande",
       groupPlayback:"Lecture", qualityLabel:"Qualité audio", qualityDesc:"Qualité du MP3",
       autoplayLabel:"Lecture automatique", autoplayDesc:"Enchaîne le titre suivant",
       volumeLabel:"Volume de départ", volumeDesc:"Volume au lancement",
       groupDownloads:"Téléchargements", folderLabel:"Dossier de téléchargement", changeBtn:"Changer",
       organizeLabel:"Ranger par playlist", organizeDesc:"Sous-dossier par playlist",
       revealLabel:"Ouvrir le dossier après téléchargement", revealDesc:"Affiche le fichier une fois terminé",
       groupData:"Données", autocheckLabel:"Vérification automatique", autocheckDesc:"Au démarrage",
       clearCacheLabel:"Nettoyer le cache temporaire", clearCacheDesc:"Fichiers audio d'écoute", cleanBtn:"Nettoyer",
       resetLabel:"Réinitialiser toutes les playlists", resetDesc:"Irréversible", resetBtn:"Tout supprimer",
       searchTitle:"Rechercher des playlists", searchPlaceholder:"Cherche une playlist, ou colle un lien YouTube...",
       searchSub:"Colle un lien de playlist YouTube (le plus fiable), ou tape un mot-clé",
       emptyTitle:"Trouve tes playlists", emptySub:"Colle un lien type youtube.com/playlist?list=... pour un résultat garanti, ou cherche par mot-clé.",
       noPlayback:"Aucune lecture en cours", prevTitle:"Précédent", playPauseTitle:"Lecture/Pause", nextTitle:"Suivant",
       downloadTrackTitle:"Télécharger ce titre", navSearch:"Rechercher", favTitle:"Tes playlists",
       favEmpty:"Aucune playlist sauvegardée. Cherche-en une et clique sur l'étoile ⭐.",
       playlistLoaded:"Playlist chargée", tracksWord:"titres", removedFromFav:"Retirée des favoris",
       addedToFav:"ajoutée à tes favoris", noTrackAvailable:"Aucun titre disponible dans cette playlist",
       addedPlaylistToFav:"Playlist ajoutée aux favoris", trackUnavailable:"Ce titre n'est pas disponible",
       playlistDeleted:"Cette playlist a été supprimée sur YouTube", playlistUpToDate:"Playlist à jour",
       playlistDeletedOrUnreachable:"Playlist supprimée ou inaccessible", checking:"Vérification en cours...",
       playbackImpossible:"Lecture impossible", downloadingTemp:"Téléchargement...", finalizing:"Finalisation...",
       retryAttempt:"Échec, nouvelle tentative", downloaded:"Téléchargé", downloadFailed:"Échec du téléchargement",
       downloadsFinished:"Téléchargement terminé", tracksProcessed:"titre(s) traité(s)",
       folderUpdated:"Dossier de téléchargement mis à jour", cacheCleared:"Cache temporaire nettoyé",
       confirmReset:"Es-tu sûr ? Toutes tes playlists sauvegardées seront supprimées définitivement.",
       allDataReset:"Toutes les données ont été réinitialisées", confirmRemoveFav:"Retirer cette playlist de tes favoris ?",
       loadFailed:"Impossible de charger", searchFailed:"Erreur de recherche", playlistLoading:"Chargement de la playlist...", genericError:"Erreur", playlistDeletedStatus:"Playlist supprimée", availableStatus:"Disponible", playlistNotFound:"Playlist introuvable, privée ou lien invalide", fetchingDetails:"Récupération des détails...", videosWord:"vidéos", linkTip:" — astuce : colle directement un lien de playlist YouTube (youtube.com/playlist?list=...) pour un résultat garanti.", noPlaylistFound:"Aucune playlist trouvée", tryOtherKeyword:"Essaie un autre mot-clé, ou vérifie l'orthographe.", playFirstTrack:"Écouter le premier titre", totalViews:"au total", deletedBadge:"Supprimée", alreadyDownloaded:"Déjà téléchargé", downloadBtn:"Télécharger", isolatedTrack:"Titre isolé", searchingFor:"Recherche de playlists pour", searchUnavailable:"Recherche indisponible", playAllTitle:"Tout lire", downloadAllBtn:"Télécharger tout", checkBtn:"Vérifier", removeBtn:"Retirer", addToFavBtn:"Ajouter aux favoris", colTitle:"Titre", colChannel:"Chaîne / Vues / Date", colDuration:"Durée", notAvailable:"Non disponible", playlistTypeLabel:"Playlist", playingNow:"Lecture en cours" },
  en:{ settingsTitle:"Settings", groupGeneral:"General", languageLabel:"Language", languageDesc:"Interface language",
       groupAppearance:"Appearance", accentLabel:"Accent color", accentDesc:"Buttons and highlights",
       densityLabel:"Card density", densityDesc:"Thumbnail size",
       densityCompact:"Compact", densityNormal:"Normal", densityLarge:"Large",
       groupPlayback:"Playback", qualityLabel:"Audio quality", qualityDesc:"MP3 quality",
       autoplayLabel:"Autoplay", autoplayDesc:"Play the next track automatically",
       volumeLabel:"Starting volume", volumeDesc:"Volume on launch",
       groupDownloads:"Downloads", folderLabel:"Download folder", changeBtn:"Change",
       organizeLabel:"Organize by playlist", organizeDesc:"Subfolder per playlist",
       revealLabel:"Open folder after download", revealDesc:"Shows the file once finished",
       groupData:"Data", autocheckLabel:"Automatic check", autocheckDesc:"On startup",
       clearCacheLabel:"Clear temporary cache", clearCacheDesc:"Listening audio files", cleanBtn:"Clear",
       resetLabel:"Reset all playlists", resetDesc:"Irreversible", resetBtn:"Delete everything",
       searchTitle:"Search playlists", searchPlaceholder:"Search for a playlist, or paste a YouTube link...",
       searchSub:"Paste a YouTube playlist link (most reliable), or type a keyword",
       emptyTitle:"Find your playlists", emptySub:"Paste a link like youtube.com/playlist?list=... for a guaranteed result, or search by keyword.",
       noPlayback:"Nothing playing", prevTitle:"Previous", playPauseTitle:"Play/Pause", nextTitle:"Next",
       downloadTrackTitle:"Download this track", navSearch:"Search", favTitle:"Your playlists",
       favEmpty:"No saved playlist. Search for one and click the star ⭐.",
       playlistLoaded:"Playlist loaded", tracksWord:"tracks", removedFromFav:"Removed from favorites",
       addedToFav:"added to your favorites", noTrackAvailable:"No track available in this playlist",
       addedPlaylistToFav:"Playlist added to favorites", trackUnavailable:"This track isn't available",
       playlistDeleted:"This playlist was deleted on YouTube", playlistUpToDate:"Playlist up to date",
       playlistDeletedOrUnreachable:"Playlist deleted or unreachable", checking:"Checking...",
       playbackImpossible:"Playback failed", downloadingTemp:"Downloading...", finalizing:"Finalizing...",
       retryAttempt:"Failed, retrying", downloaded:"Downloaded", downloadFailed:"Download failed",
       downloadsFinished:"Download finished", tracksProcessed:"track(s) processed",
       folderUpdated:"Download folder updated", cacheCleared:"Temporary cache cleared",
       confirmReset:"Are you sure? All your saved playlists will be permanently deleted.",
       allDataReset:"All data has been reset", confirmRemoveFav:"Remove this playlist from your favorites?",
       loadFailed:"Unable to load", searchFailed:"Search error", playlistLoading:"Loading playlist...", genericError:"Error", playlistDeletedStatus:"Playlist deleted", availableStatus:"Available", playlistNotFound:"Playlist not found, private, or invalid link", fetchingDetails:"Fetching details...", videosWord:"videos", linkTip:" — tip: paste a YouTube playlist link directly (youtube.com/playlist?list=...) for a guaranteed result.", noPlaylistFound:"No playlist found", tryOtherKeyword:"Try another keyword, or check the spelling.", playFirstTrack:"Play the first track", totalViews:"total", deletedBadge:"Deleted", alreadyDownloaded:"Already downloaded", downloadBtn:"Download", isolatedTrack:"Single track", searchingFor:"Searching playlists for", searchUnavailable:"Search unavailable", playAllTitle:"Play all", downloadAllBtn:"Download all", checkBtn:"Check", removeBtn:"Remove", addToFavBtn:"Add to favorites", colTitle:"Title", colChannel:"Channel / Views / Date", colDuration:"Duration", notAvailable:"Not available", playlistTypeLabel:"Playlist", playingNow:"Now playing" },
  de:{ settingsTitle:"Einstellungen", groupGeneral:"Allgemein", languageLabel:"Sprache", languageDesc:"Oberflächensprache",
       groupAppearance:"Erscheinungsbild", accentLabel:"Akzentfarbe", accentDesc:"Schaltflächen und Hervorhebungen",
       densityLabel:"Kartendichte", densityDesc:"Größe der Vorschaubilder",
       densityCompact:"Kompakt", densityNormal:"Normal", densityLarge:"Groß",
       groupPlayback:"Wiedergabe", qualityLabel:"Audioqualität", qualityDesc:"MP3-Qualität",
       autoplayLabel:"Automatische Wiedergabe", autoplayDesc:"Spielt den nächsten Titel automatisch ab",
       volumeLabel:"Startlautstärke", volumeDesc:"Lautstärke beim Start",
       groupDownloads:"Downloads", folderLabel:"Download-Ordner", changeBtn:"Ändern",
       organizeLabel:"Nach Playlist ordnen", organizeDesc:"Unterordner pro Playlist",
       revealLabel:"Ordner nach Download öffnen", revealDesc:"Zeigt die Datei nach Abschluss",
       groupData:"Daten", autocheckLabel:"Automatische Prüfung", autocheckDesc:"Beim Start",
       clearCacheLabel:"Temporären Cache leeren", clearCacheDesc:"Audiodateien zum Anhören", cleanBtn:"Leeren",
       resetLabel:"Alle Playlists zurücksetzen", resetDesc:"Unwiderruflich", resetBtn:"Alles löschen",
       searchTitle:"Playlists suchen", searchPlaceholder:"Playlist suchen oder YouTube-Link einfügen...",
       searchSub:"Füge einen YouTube-Playlist-Link ein (am zuverlässigsten) oder gib ein Stichwort ein",
       emptyTitle:"Finde deine Playlists", emptySub:"Füge einen Link wie youtube.com/playlist?list=... für ein garantiertes Ergebnis ein oder suche nach einem Stichwort.",
       noPlayback:"Keine Wiedergabe", prevTitle:"Zurück", playPauseTitle:"Wiedergabe/Pause", nextTitle:"Weiter",
       downloadTrackTitle:"Diesen Titel herunterladen", navSearch:"Suchen", favTitle:"Deine Playlists",
       favEmpty:"Keine gespeicherte Playlist. Suche eine und klicke auf den Stern ⭐.",
       playlistLoaded:"Playlist geladen", tracksWord:"Titel", removedFromFav:"Aus Favoriten entfernt",
       addedToFav:"zu deinen Favoriten hinzugefügt", noTrackAvailable:"Kein Titel in dieser Playlist verfügbar",
       addedPlaylistToFav:"Playlist zu Favoriten hinzugefügt", trackUnavailable:"Dieser Titel ist nicht verfügbar",
       playlistDeleted:"Diese Playlist wurde auf YouTube gelöscht", playlistUpToDate:"Playlist aktuell",
       playlistDeletedOrUnreachable:"Playlist gelöscht oder nicht erreichbar", checking:"Überprüfung läuft...",
       playbackImpossible:"Wiedergabe fehlgeschlagen", downloadingTemp:"Wird heruntergeladen...", finalizing:"Abschließen...",
       retryAttempt:"Fehlgeschlagen, erneuter Versuch", downloaded:"Heruntergeladen", downloadFailed:"Download fehlgeschlagen",
       downloadsFinished:"Download abgeschlossen", tracksProcessed:"Titel verarbeitet",
       folderUpdated:"Download-Ordner aktualisiert", cacheCleared:"Temporärer Cache geleert",
       confirmReset:"Bist du sicher? Alle gespeicherten Playlists werden endgültig gelöscht.",
       allDataReset:"Alle Daten wurden zurückgesetzt", confirmRemoveFav:"Diese Playlist aus deinen Favoriten entfernen?",
       loadFailed:"Laden nicht möglich", searchFailed:"Suchfehler", playlistLoading:"Playlist wird geladen...", genericError:"Fehler", playlistDeletedStatus:"Playlist gelöscht", availableStatus:"Verfügbar", playlistNotFound:"Playlist nicht gefunden, privat oder ungültiger Link", fetchingDetails:"Details werden abgerufen...", videosWord:"Videos", linkTip:" — Tipp: Füge direkt einen YouTube-Playlist-Link ein (youtube.com/playlist?list=...) für ein garantiertes Ergebnis.", noPlaylistFound:"Keine Playlist gefunden", tryOtherKeyword:"Versuche ein anderes Stichwort oder überprüfe die Schreibweise.", playFirstTrack:"Ersten Titel abspielen", totalViews:"insgesamt", deletedBadge:"Gelöscht", alreadyDownloaded:"Bereits heruntergeladen", downloadBtn:"Herunterladen", isolatedTrack:"Einzelner Titel", searchingFor:"Suche nach Playlists für", searchUnavailable:"Suche nicht verfügbar", playAllTitle:"Alle abspielen", downloadAllBtn:"Alle herunterladen", checkBtn:"Prüfen", removeBtn:"Entfernen", addToFavBtn:"Zu Favoriten hinzufügen", colTitle:"Titel", colChannel:"Kanal / Aufrufe / Datum", colDuration:"Dauer", notAvailable:"Nicht verfügbar", playlistTypeLabel:"Playlist", playingNow:"Wird wiedergegeben" },
  es:{ settingsTitle:"Ajustes", groupGeneral:"General", languageLabel:"Idioma", languageDesc:"Idioma de la interfaz",
       groupAppearance:"Apariencia", accentLabel:"Color de acento", accentDesc:"Botones y resaltados",
       densityLabel:"Densidad de tarjetas", densityDesc:"Tamaño de las miniaturas",
       densityCompact:"Compacta", densityNormal:"Normal", densityLarge:"Grande",
       groupPlayback:"Reproducción", qualityLabel:"Calidad de audio", qualityDesc:"Calidad del MP3",
       autoplayLabel:"Reproducción automática", autoplayDesc:"Encadena la siguiente pista",
       volumeLabel:"Volumen inicial", volumeDesc:"Volumen al iniciar",
       groupDownloads:"Descargas", folderLabel:"Carpeta de descargas", changeBtn:"Cambiar",
       organizeLabel:"Organizar por playlist", organizeDesc:"Subcarpeta por playlist",
       revealLabel:"Abrir carpeta tras la descarga", revealDesc:"Muestra el archivo al terminar",
       groupData:"Datos", autocheckLabel:"Comprobación automática", autocheckDesc:"Al iniciar",
       clearCacheLabel:"Limpiar caché temporal", clearCacheDesc:"Archivos de audio de escucha", cleanBtn:"Limpiar",
       resetLabel:"Restablecer todas las playlists", resetDesc:"Irreversible", resetBtn:"Eliminar todo",
       searchTitle:"Buscar playlists", searchPlaceholder:"Busca una playlist o pega un enlace de YouTube...",
       searchSub:"Pega un enlace de playlist de YouTube (lo más fiable) o escribe una palabra clave",
       emptyTitle:"Encuentra tus playlists", emptySub:"Pega un enlace tipo youtube.com/playlist?list=... para un resultado garantizado, o busca por palabra clave.",
       noPlayback:"Sin reproducción", prevTitle:"Anterior", playPauseTitle:"Reproducir/Pausar", nextTitle:"Siguiente",
       downloadTrackTitle:"Descargar esta pista", navSearch:"Buscar", favTitle:"Tus playlists",
       favEmpty:"Ninguna playlist guardada. Busca una y haz clic en la estrella ⭐.",
       playlistLoaded:"Playlist cargada", tracksWord:"pistas", removedFromFav:"Eliminada de favoritos",
       addedToFav:"añadida a tus favoritos", noTrackAvailable:"Ninguna pista disponible en esta playlist",
       addedPlaylistToFav:"Playlist añadida a favoritos", trackUnavailable:"Esta pista no está disponible",
       playlistDeleted:"Esta playlist fue eliminada en YouTube", playlistUpToDate:"Playlist actualizada",
       playlistDeletedOrUnreachable:"Playlist eliminada o inaccesible", checking:"Comprobando...",
       playbackImpossible:"Reproducción fallida", downloadingTemp:"Descargando...", finalizing:"Finalizando...",
       retryAttempt:"Fallo, reintentando", downloaded:"Descargado", downloadFailed:"Descarga fallida",
       downloadsFinished:"Descarga finalizada", tracksProcessed:"pista(s) procesada(s)",
       folderUpdated:"Carpeta de descargas actualizada", cacheCleared:"Caché temporal limpiada",
       confirmReset:"¿Seguro? Todas tus playlists guardadas se eliminarán permanentemente.",
       allDataReset:"Todos los datos han sido restablecidos", confirmRemoveFav:"¿Eliminar esta playlist de tus favoritos?",
       loadFailed:"No se pudo cargar", searchFailed:"Error de búsqueda", playlistLoading:"Cargando playlist...", genericError:"Error", playlistDeletedStatus:"Playlist eliminada", availableStatus:"Disponible", playlistNotFound:"Playlist no encontrada, privada o enlace inválido", fetchingDetails:"Obteniendo detalles...", videosWord:"vídeos", linkTip:" — consejo: pega directamente un enlace de playlist de YouTube (youtube.com/playlist?list=...) para un resultado garantizado.", noPlaylistFound:"No se encontró ninguna playlist", tryOtherKeyword:"Prueba otra palabra clave o revisa la ortografía.", playFirstTrack:"Reproducir la primera pista", totalViews:"en total", deletedBadge:"Eliminada", alreadyDownloaded:"Ya descargado", downloadBtn:"Descargar", isolatedTrack:"Pista suelta", searchingFor:"Buscando playlists para", searchUnavailable:"Búsqueda no disponible", playAllTitle:"Reproducir todo", downloadAllBtn:"Descargar todo", checkBtn:"Comprobar", removeBtn:"Quitar", addToFavBtn:"Añadir a favoritos", colTitle:"Título", colChannel:"Canal / Vistas / Fecha", colDuration:"Duración", notAvailable:"No disponible", playlistTypeLabel:"Playlist", playingNow:"Reproduciendo ahora" },
  ja:{ settingsTitle:"設定", groupGeneral:"一般", languageLabel:"言語", languageDesc:"インターフェースの言語",
       groupAppearance:"外観", accentLabel:"アクセントカラー", accentDesc:"ボタンとハイライト",
       densityLabel:"カードの密度", densityDesc:"サムネイルのサイズ",
       densityCompact:"コンパクト", densityNormal:"標準", densityLarge:"大",
       groupPlayback:"再生", qualityLabel:"音質", qualityDesc:"MP3の品質",
       autoplayLabel:"自動再生", autoplayDesc:"次の曲を自動的に再生",
       volumeLabel:"初期音量", volumeDesc:"起動時の音量",
       groupDownloads:"ダウンロード", folderLabel:"ダウンロードフォルダ", changeBtn:"変更",
       organizeLabel:"プレイリストごとに整理", organizeDesc:"プレイリストごとのサブフォルダ",
       revealLabel:"ダウンロード後にフォルダを開く", revealDesc:"完了後にファイルを表示",
       groupData:"データ", autocheckLabel:"自動チェック", autocheckDesc:"起動時",
       clearCacheLabel:"一時キャッシュを削除", clearCacheDesc:"再生用の音声ファイル", cleanBtn:"削除",
       resetLabel:"すべてのプレイリストをリセット", resetDesc:"元に戻せません", resetBtn:"すべて削除",
       searchTitle:"プレイリストを検索", searchPlaceholder:"プレイリストを検索、またはYouTubeリンクを貼り付け...",
       searchSub:"YouTubeプレイリストのリンクを貼り付ける（最も確実）か、キーワードを入力",
       emptyTitle:"プレイリストを見つけよう", emptySub:"確実な結果を得るには youtube.com/playlist?list=... のようなリンクを貼り付けるか、キーワードで検索してください。",
       noPlayback:"再生していません", prevTitle:"前へ", playPauseTitle:"再生/一時停止", nextTitle:"次へ",
       downloadTrackTitle:"この曲をダウンロード", navSearch:"検索", favTitle:"あなたのプレイリスト",
       favEmpty:"保存されたプレイリストはありません。検索して星⭐をクリックしてください。",
       playlistLoaded:"プレイリストを読み込みました", tracksWord:"曲", removedFromFav:"お気に入りから削除しました",
       addedToFav:"をお気に入りに追加しました", noTrackAvailable:"このプレイリストに利用可能な曲がありません",
       addedPlaylistToFav:"プレイリストをお気に入りに追加しました", trackUnavailable:"この曲は利用できません",
       playlistDeleted:"このプレイリストはYouTubeで削除されました", playlistUpToDate:"プレイリストは最新です",
       playlistDeletedOrUnreachable:"プレイリストが削除されたかアクセスできません", checking:"確認中...",
       playbackImpossible:"再生できません", downloadingTemp:"ダウンロード中...", finalizing:"仕上げ中...",
       retryAttempt:"失敗、再試行中", downloaded:"ダウンロード済み", downloadFailed:"ダウンロード失敗",
       downloadsFinished:"ダウンロード完了", tracksProcessed:"曲を処理しました",
       folderUpdated:"ダウンロードフォルダを更新しました", cacheCleared:"一時キャッシュを削除しました",
       confirmReset:"本当によろしいですか？保存されたすべてのプレイリストが完全に削除されます。",
       allDataReset:"すべてのデータがリセットされました", confirmRemoveFav:"このプレイリストをお気に入りから削除しますか？",
       loadFailed:"読み込めません", searchFailed:"検索エラー", playlistLoading:"プレイリストを読み込み中...", genericError:"エラー", playlistDeletedStatus:"プレイリスト削除済み", availableStatus:"利用可能", playlistNotFound:"プレイリストが見つからないか、非公開か、リンクが無効です", fetchingDetails:"詳細を取得中...", videosWord:"本の動画", linkTip:" — ヒント：確実な結果を得るには、YouTubeプレイリストのリンク（youtube.com/playlist?list=...）を直接貼り付けてください。", noPlaylistFound:"プレイリストが見つかりません", tryOtherKeyword:"別のキーワードを試すか、スペルを確認してください。", playFirstTrack:"最初の曲を再生", totalViews:"合計", deletedBadge:"削除済み", alreadyDownloaded:"ダウンロード済み", downloadBtn:"ダウンロード", isolatedTrack:"単曲", searchingFor:"プレイリストを検索中", searchUnavailable:"検索できません", playAllTitle:"すべて再生", downloadAllBtn:"すべてダウンロード", checkBtn:"確認", removeBtn:"削除", addToFavBtn:"お気に入りに追加", colTitle:"タイトル", colChannel:"チャンネル / 再生数 / 日付", colDuration:"長さ", notAvailable:"利用不可", playlistTypeLabel:"プレイリスト", playingNow:"再生中" },
  ru:{ settingsTitle:"Настройки", groupGeneral:"Общие", languageLabel:"Язык", languageDesc:"Язык интерфейса",
       groupAppearance:"Внешний вид", accentLabel:"Акцентный цвет", accentDesc:"Кнопки и выделения",
       densityLabel:"Плотность карточек", densityDesc:"Размер миниатюр",
       densityCompact:"Компактно", densityNormal:"Обычно", densityLarge:"Крупно",
       groupPlayback:"Воспроизведение", qualityLabel:"Качество звука", qualityDesc:"Качество MP3",
       autoplayLabel:"Автовоспроизведение", autoplayDesc:"Автоматически включает следующий трек",
       volumeLabel:"Начальная громкость", volumeDesc:"Громкость при запуске",
       groupDownloads:"Загрузки", folderLabel:"Папка загрузок", changeBtn:"Изменить",
       organizeLabel:"Сортировать по плейлистам", organizeDesc:"Подпапка для каждого плейлиста",
       revealLabel:"Открыть папку после загрузки", revealDesc:"Показывает файл по завершении",
       groupData:"Данные", autocheckLabel:"Автопроверка", autocheckDesc:"При запуске",
       clearCacheLabel:"Очистить временный кэш", clearCacheDesc:"Аудиофайлы прослушивания", cleanBtn:"Очистить",
       resetLabel:"Сбросить все плейлисты", resetDesc:"Необратимо", resetBtn:"Удалить всё",
       searchTitle:"Поиск плейлистов", searchPlaceholder:"Найти плейлист или вставить ссылку YouTube...",
       searchSub:"Вставьте ссылку на плейлист YouTube (самый надёжный способ) или введите ключевое слово",
       emptyTitle:"Найдите свои плейлисты", emptySub:"Вставьте ссылку вида youtube.com/playlist?list=... для гарантированного результата, или выполните поиск по ключевому слову.",
       noPlayback:"Ничего не воспроизводится", prevTitle:"Назад", playPauseTitle:"Воспроизведение/Пауза", nextTitle:"Вперёд",
       downloadTrackTitle:"Скачать этот трек", navSearch:"Поиск", favTitle:"Ваши плейлисты",
       favEmpty:"Нет сохранённых плейлистов. Найдите один и нажмите на звёздочку ⭐.",
       playlistLoaded:"Плейлист загружен", tracksWord:"треков", removedFromFav:"Удалено из избранного",
       addedToFav:"добавлено в избранное", noTrackAvailable:"В этом плейлисте нет доступных треков",
       addedPlaylistToFav:"Плейлист добавлен в избранное", trackUnavailable:"Этот трек недоступен",
       playlistDeleted:"Этот плейлист был удалён на YouTube", playlistUpToDate:"Плейлист актуален",
       playlistDeletedOrUnreachable:"Плейлист удалён или недоступен", checking:"Проверка...",
       playbackImpossible:"Не удалось воспроизвести", downloadingTemp:"Загрузка...", finalizing:"Завершение...",
       retryAttempt:"Ошибка, повторная попытка", downloaded:"Загружено", downloadFailed:"Ошибка загрузки",
       downloadsFinished:"Загрузка завершена", tracksProcessed:"трек(ов) обработано",
       folderUpdated:"Папка загрузок обновлена", cacheCleared:"Временный кэш очищен",
       confirmReset:"Вы уверены? Все сохранённые плейлисты будут удалены безвозвратно.",
       allDataReset:"Все данные были сброшены", confirmRemoveFav:"Удалить этот плейлист из избранного?",
       loadFailed:"Не удалось загрузить", searchFailed:"Ошибка поиска", playlistLoading:"Загрузка плейлиста...", genericError:"Ошибка", playlistDeletedStatus:"Плейлист удалён", availableStatus:"Доступен", playlistNotFound:"Плейлист не найден, приватный или неверная ссылка", fetchingDetails:"Получение данных...", videosWord:"видео", linkTip:" — совет: вставьте прямую ссылку на плейлист YouTube (youtube.com/playlist?list=...) для гарантированного результата.", noPlaylistFound:"Плейлист не найден", tryOtherKeyword:"Попробуйте другое ключевое слово или проверьте написание.", playFirstTrack:"Воспроизвести первый трек", totalViews:"всего", deletedBadge:"Удалён", alreadyDownloaded:"Уже загружено", downloadBtn:"Скачать", isolatedTrack:"Отдельный трек", searchingFor:"Поиск плейлистов по запросу", searchUnavailable:"Поиск недоступен", playAllTitle:"Воспроизвести всё", downloadAllBtn:"Скачать всё", checkBtn:"Проверить", removeBtn:"Удалить", addToFavBtn:"Добавить в избранное", colTitle:"Название", colChannel:"Канал / Просмотры / Дата", colDuration:"Длительность", notAvailable:"Недоступно", playlistTypeLabel:"Плейлист", playingNow:"Сейчас играет" },
};
function applyLanguage(lang){
  const dict = I18N[lang] || I18N.fr;
  document.documentElement.lang = lang;
  document.querySelectorAll("[data-i18n]").forEach(el=>{
    const key = el.getAttribute("data-i18n");
    if(dict[key] !== undefined) el.textContent = dict[key];
  });
  document.querySelectorAll("[data-i18n-placeholder]").forEach(el=>{
    const key = el.getAttribute("data-i18n-placeholder");
    if(dict[key] !== undefined) el.placeholder = dict[key];
  });
  document.querySelectorAll("[data-i18n-title]").forEach(el=>{
    const key = el.getAttribute("data-i18n-title");
    if(dict[key] !== undefined) el.title = dict[key];
  });
  // ré-affiche les vues dynamiques déjà rendues (liste de favoris, détail playlist)
  if(typeof renderFavorites === "function") renderFavorites();
  if(state.currentPlaylistId && state.favorites[state.currentPlaylistId] && typeof renderPlaylistDetail === "function"){
    renderPlaylistDetail(state.favorites[state.currentPlaylistId], true);
  }
}
function t(key){ const dict = I18N[state.settings.language] || I18N.fr; return dict[key] !== undefined ? dict[key] : (I18N.fr[key]||key); }

/* ---------- Pont vers le lecteur audio Python (pygame) ----------
   La lecture réelle se fait côté Python (pygame.mixer), car WebView2 (Windows)
   refuse de charger des fichiers audio locaux dans une balise <audio>.
   Cet objet "audio" imite l'API HTMLMediaElement minimale utilisée plus bas,
   pour ne pas avoir à réécrire toute la logique de lecture. */
const audio = {
  _duration: 0, _currentTime: 0, _volume: 0.8, _paused: true, _listeners: {},
  get duration(){ return this._duration; },
  get currentTime(){ return this._currentTime; },
  set currentTime(v){ this._currentTime = v; api("seek_audio", v); },
  get volume(){ return this._volume; },
  set volume(v){ this._volume = v; api("set_volume", v); },
  get paused(){ return this._paused; },
  get src(){ return this._src || ""; },
  set src(v){ this._src = v; },
  async play(){ this._paused = false; await api("resume_audio"); },
  pause(){ this._paused = true; api("pause_audio"); },
  addEventListener(evt, cb){ (this._listeners[evt] ||= []).push(cb); },
  _emit(evt, data){ (this._listeners[evt]||[]).forEach(cb=>cb(data)); }
};
/* Appelé depuis Python (evaluate_js) à intervalle régulier pendant la lecture. */
window.onPlayerTick = function(currentTime, duration, ended){
  audio._currentTime = currentTime; audio._duration = duration;
  audio._emit("timeupdate");
  if(ended){ audio._paused = true; audio._emit("ended"); }
};

function backendReady(){ return new Promise(res=>{ if(window.pywebview&&window.pywebview.api) return res(); window.addEventListener("pywebviewready",()=>res()); }); }
async function api(method, ...args){ await backendReady(); return window.pywebview.api[method](...args); }
const $ = s => document.querySelector(s);
const $all = s => Array.from(document.querySelectorAll(s));
function escapeHtml(s){ const d=document.createElement("div"); d.textContent=s??""; return d.innerHTML; }

function showToast(msg,type="normal",duration=3000){
  const t=$("#toast"); t.textContent=msg; t.className="show"+(type!=="normal"?" "+type:"");
  clearTimeout(showToast._t); showToast._t=setTimeout(()=>t.classList.remove("show"),duration);
}
window.showToast = showToast;
function playerToast(msg,duration=2500){
  const t=$("#player-toast"); $("#player-toast-text").textContent=msg;
  $("#player-toast-bar").classList.add("hidden");
  t.classList.add("show");
  clearTimeout(playerToast._t);
  if(duration>0) playerToast._t=setTimeout(()=>t.classList.remove("show"),duration);
}
/* Affiche/actualise la barre de progression du téléchargement en cours (0-100, ou null pour cacher). */
function playerToastProgress(msg,pct){
  const t=$("#player-toast"); $("#player-toast-text").textContent=msg;
  clearTimeout(playerToast._t);
  t.classList.add("show");
  const bar=$("#player-toast-bar"), fill=$("#player-toast-bar-fill");
  if(pct==null){ bar.classList.add("hidden"); return; }
  bar.classList.remove("hidden");
  fill.style.width=Math.max(0,Math.min(100,pct))+"%";
}
/* Appelé depuis Python (evaluate_js) pendant le téléchargement temporaire d'une piste.
   bytesTransferred = octets réellement transités (cumulés sur toutes les tentatives).
   retry != null signale une tentative ratée (retry = numéro de la tentative qui vient d'échouer). */
function formatBytes(n){
  if(!n) return "0 Ko";
  if(n>=1024*1024) return (n/1024/1024).toFixed(1)+" Mo";
  return (n/1024).toFixed(0)+" Ko";
}
window.onDownloadProgress = function(pct, speedText, bytesTransferred, retry, error){
  if(retry!=null){
    playerToastProgress(`${t("retryAttempt")} (${retry}/3)...`, 0);
    return;
  }
  const sizeTxt = formatBytes(bytesTransferred);
  if(pct>=100){ playerToastProgress(`${t("finalizing")} ${sizeTxt}`,100); return; }
  playerToastProgress(`${t("downloadingTemp")} ${pct.toFixed(0)}% · ${sizeTxt}${speedText?` (${speedText})`:""}`, pct);
};
function formatDuration(sec){
  if(!sec) return "--:--"; sec=Math.floor(sec);
  const h=Math.floor(sec/3600), m=Math.floor((sec%3600)/60), s=sec%60;
  return h ? `${h}:${String(m).padStart(2,"0")}:${String(s).padStart(2,"0")}` : `${m}:${String(s).padStart(2,"0")}`;
}
function switchView(name){ $all(".view").forEach(v=>v.classList.remove("active")); $("#view-"+name).classList.add("active"); }
function errorBlock(title,err){
  return `<div class="empty-state"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>
    <div class="empty-state-title">${title}</div><div class="empty-state-sub">${escapeHtml(String(err))}</div></div>`;
}

/* ---------- Favoris ---------- */
function renderFavorites(){
  const list=$("#fav-list"); const ids=Object.keys(state.favorites);
  if(!ids.length){ list.innerHTML=`<div class="empty-fav">${t("favEmpty")}</div>`; return; }
  list.innerHTML="";
  ids.forEach(pid=>{
    const pl=state.favorites[pid], deleted=pl.status==="deleted";
    const el=document.createElement("div");
    el.className="fav-item"+(deleted?" deleted":"")+(state.currentPlaylistId===pid?" selected":"");
    el.innerHTML=`<div class="fav-cover"${pl.thumbnail?` style="background-image:url('${escapeHtml(pl.thumbnail)}');background-size:cover;background-position:center"`:""}>${pl.thumbnail?"":"🎵"}</div><div class="fav-info"><div class="fav-name">${escapeHtml(pl.title)}</div>
      <div class="fav-sub">${pl.tracks.length} titres</div></div>
      <div class="status-dot" title="${deleted?t("playlistDeletedStatus"):t("availableStatus")}"></div>`;
    el.addEventListener("click",()=>openPlaylistDetail(pid));
    list.appendChild(el);
  });
}

/* ---------- Recherche ---------- */
function looksLikePlaylistLink(t){ return /youtube\\.com\\/(playlist|watch)\\?.*list=/.test(t) || /youtu\\.be\\/.*list=/.test(t); }
$("#search-input").addEventListener("keydown", e=>{ if(e.key==="Enter") doSearchOrLink(); });

async function doSearchOrLink(){
  const q=$("#search-input").value.trim(); if(!q) return;
  if(looksLikePlaylistLink(q)) return openPlaylistFromLink(q);
  return doSearch(q);
}

async function openPlaylistFromLink(url){
  switchView("playlist");
  const el=$("#playlist-detail-content");
  renderFetchProgress(el,0,1,"Lecture du lien...");
  window.onPlaylistFetchProgress=(done,total)=>renderFetchProgress(el,done,total);
  try{
    const details=await api("add_playlist_from_link",url);
    if(!details) throw new Error(t("playlistNotFound"));
    renderPlaylistDetail(details, !!state.favorites[details.id]);
    showToast(`${t("playlistLoaded")} : ${details.video_count} ${t("tracksWord")}`);
  }catch(err){ el.innerHTML=errorBlock("Impossible de charger ce lien",err); }
  finally{ window.onPlaylistFetchProgress=null; }
}

function renderFetchProgress(container,done,total,label){
  const pct=total?Math.round((done/total)*100):0;
  container.innerHTML=`<div class="fetch-progress-wrap"><div class="spinner"></div>
    <div class="fetch-progress-text">${label||`${t("fetchingDetails")} ${done}/${total} ${t("videosWord")}`}</div>
    <div class="fetch-progress-bar"><div class="fetch-progress-fill" style="width:${pct}%"></div></div></div>`;
}

async function doSearch(q){
  switchView("search");
  const container=$("#search-results");
  container.innerHTML=`<div class="loading-row"><div class="spinner"></div> ${t("searchingFor")} « ${escapeHtml(q)} »...</div>`;
  try{
    const results=await api("search_playlists",q);
    renderSearchResults(results,q);
  }catch(err){
    container.innerHTML=errorBlock(t("searchUnavailable"),
      String(err)+t("linkTip"));
  }
}

function renderSearchResults(results,query){
  const container=$("#search-results");
  $(".view-title").textContent=`Résultats pour « ${query} »`;
  if(!results.length){
    container.innerHTML=`<div class="empty-state"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><circle cx="11" cy="11" r="7"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>
      <div class="empty-state-title">${t("noPlaylistFound")}</div><div class="empty-state-sub">${t("tryOtherKeyword")}</div></div>`;
    return;
  }
  const grid=document.createElement("div"); grid.className="card-grid";
  results.forEach(pl=>{
    const saved=!!state.favorites[pl.id];
    const card=document.createElement("div"); card.className="pl-card";
    card.innerHTML=`<div class="pl-cover"${pl.thumbnail?` style="background-image:url('${escapeHtml(pl.thumbnail)}');background-size:cover;background-position:center"`:""}>${pl.thumbnail?"":"🎵"}<button class="pl-play-fab" title="${t("playFirstTrack")}"><svg viewBox="0 0 24 24" fill="currentColor"><path d="M8 5v14l11-7z"/></svg></button></div>
      <button class="pl-star-btn ${saved?"saved":""}" title="Ajouter aux favoris"><svg viewBox="0 0 24 24" fill="${saved?"currentColor":"none"}" stroke="currentColor" stroke-width="2"><polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/></svg></button>
      <div class="pl-name">${escapeHtml(pl.title)}</div><div class="pl-channel">${escapeHtml(pl.channel)}</div>
      <div class="pl-meta-line">${pl.video_count?pl.video_count+" "+t("videosWord"):""}</div>`;
    card.querySelector(".pl-star-btn").addEventListener("click",e=>{ e.stopPropagation(); toggleSavePlaylist(pl,card.querySelector(".pl-star-btn")); });
    card.querySelector(".pl-play-fab").addEventListener("click",e=>{ e.stopPropagation(); playFirstTrackOfPlaylist(pl); });
    card.addEventListener("click",()=>openSearchPlaylistDetail(pl));
    grid.appendChild(card);
  });
  container.innerHTML=""; container.appendChild(grid);
}

async function toggleSavePlaylist(plStub,btnEl){
  if(state.favorites[plStub.id]){
    await api("remove_playlist",plStub.id);
    delete state.favorites[plStub.id];
    btnEl.classList.remove("saved"); btnEl.querySelector("svg").setAttribute("fill","none");
    showToast(t("removedFromFav")); renderFavorites(); return;
  }
  btnEl.innerHTML=`<div class="spinner"></div>`;
  try{
    const stub=await api("fetch_playlist_stub",plStub.url);
    if(!stub) throw new Error("Playlist introuvable");
    await api("save_playlist",stub);
    state.favorites[stub.id]=stub;
    showToast(`« ${stub.title} » ${t("addedToFav")}`);
    renderFavorites();
    // si l'utilisateur est déjà sur cette playlist (ouverte depuis la recherche), on
    // continue d'enrichir les pistes en tâche de fond sans le faire attendre
    if(state.currentPlaylistId===stub.id) loadTracksProgressively(stub);
  }catch(err){ showToast(t("genericError")+" : "+err,"danger"); }
  finally{
    btnEl.innerHTML=`<svg viewBox="0 0 24 24" fill="${state.favorites[plStub.id]?"currentColor":"none"}" stroke="currentColor" stroke-width="2"><polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/></svg>`;
    btnEl.classList.toggle("saved", !!state.favorites[plStub.id]);
  }
}

async function playFirstTrackOfPlaylist(plStub){
  playerToast(t("playlistLoading")||"Chargement de la playlist...");
  try{
    const stub=await api("fetch_playlist_stub",plStub.url);
    const first = stub && stub.tracks.find(tr=>tr.downloadable);
    if(!stub || !first) throw new Error("Aucun titre lisible dans cette playlist");
    state.queue=stub.tracks; state.queueIndex=stub.tracks.indexOf(first);
    playTrackAtQueueIndex(state.queueIndex,stub);
  }catch(err){ showToast(t("loadFailed")+" : "+err,"danger"); }
}

async function openSearchPlaylistDetail(plStub){
  switchView("playlist");
  const el=$("#playlist-detail-content");
  renderFetchProgress(el,0,1,"Chargement de la playlist...");
  try{
    const stub=await api("fetch_playlist_stub",plStub.url);
    if(!stub) throw new Error(t("playlistDeleted"));
    renderPlaylistDetail(stub, !!state.favorites[stub.id]);
    loadTracksProgressively(stub);
  }catch(err){ el.innerHTML=errorBlock("Playlist introuvable",err); }
}

/* Complète les infos des pistes (durée réelle, vues, disponibilité...) par lots de 10,
   en mettant à jour chaque ligne du tableau au fur et à mesure — l'utilisateur voit la
   playlist et peut déjà cliquer dessus sans attendre le chargement complet. */
async function loadTracksProgressively(pl){
  const batchSize=10;
  for(let i=0;i<pl.tracks.length;i+=batchSize){
    const batch=pl.tracks.slice(i,i+batchSize);
    let detailed;
    try{ detailed=await api("fetch_track_batch",batch); }
    catch(err){ continue; } // on ignore le lot en échec, le reste continue de charger
    detailed.forEach((t,j)=>{
      pl.tracks[i+j]=t;
      const row=document.querySelector(`.track-row[data-track-id="${CSS.escape(String(t.id))}"]`);
      if(row) row.replaceWith(renderTrackRow(t,i+j,pl));
    });
    // sauvegarde incrémentale si la playlist est déjà en favoris, pour ne rien perdre
    if(state.favorites[pl.id]) api("save_playlist",pl);
  }
}

/* ---------- Détail playlist ---------- */
async function openPlaylistDetail(pid){
  state.currentPlaylistId=pid; renderFavorites(); switchView("playlist");
  const pl=state.favorites[pid];
  renderPlaylistDetail(pl, true);
  if(pl.tracks.some(t=>!t.detailed)) loadTracksProgressively(pl);
}

function renderPlaylistDetail(pl,isSaved){
  const el=$("#playlist-detail-content");
  const deleted=pl.status==="deleted";
  const saved=isSaved || !!state.favorites[pl.id];

  el.innerHTML=`
    <div class="pl-detail-header"><div class="pl-detail-cover"${pl.thumbnail?` style="background-image:url('${escapeHtml(pl.thumbnail)}');background-size:cover;background-position:center"`:""}>${pl.thumbnail?"":"🎵"}</div>
      <div class="pl-detail-meta"><div class="pl-detail-type">${t("playlistTypeLabel")}</div>
        <div class="pl-detail-title">${escapeHtml(pl.title)}</div>
        <div class="pl-detail-sub">${escapeHtml(pl.channel)} • ${pl.video_count??pl.tracks.length} ${t("videosWord")}${pl.total_views_display?" • "+pl.total_views_display+" "+t("totalViews"):""}
          ${deleted?`<span class="status-badge deleted">${t("deletedBadge")}</span>`:""}</div></div></div>
    <div class="pl-detail-actions">
      <button class="play-all-btn" id="play-all-btn" title="${t("playAllTitle")}"><svg viewBox="0 0 24 24" fill="currentColor"><path d="M8 5v14l11-7z"/></svg></button>
      <button class="dl-all-btn" id="dl-all-btn"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>${t("downloadAllBtn")}</button>
      ${saved?`
        <button class="recheck-btn" id="recheck-one-btn"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M23 4v6h-6"/><path d="M1 20v-6h6"/><path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15"/></svg>${t("checkBtn")}</button>
        <button class="remove-fav-btn" id="remove-fav-btn"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 6h18"/><path d="M8 6V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/><path d="M19 6l-1 14a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2L5 6"/></svg>${t("removeBtn")}</button>
      `:`
        <button class="recheck-btn" id="save-from-detail-btn"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/></svg>${t("addToFavBtn")}</button>
      `}
    </div>
    <div class="track-table" id="track-table"><div class="track-row header-row"><div>#</div><div>${t("colTitle")}</div><div>${t("colChannel")}</div><div>${t("colDuration")}</div><div></div></div></div>`;

  const table=$("#track-table");
  pl.tracks.forEach((tr,idx)=>table.appendChild(renderTrackRow(tr,idx,pl)));

  $("#play-all-btn").addEventListener("click",()=>{
    const playable=pl.tracks.filter(t=>t.downloadable);
    if(!playable.length) return showToast(t("noTrackAvailable"),"warning");
    state.queue=pl.tracks; state.queueIndex=pl.tracks.indexOf(playable[0]);
    playTrackAtQueueIndex(state.queueIndex,pl);
  });
  $("#dl-all-btn").addEventListener("click",()=>downloadWholePlaylist(pl));
  if(saved){
    $("#recheck-one-btn")?.addEventListener("click",()=>recheckOnePlaylist(pl.id));
    $("#remove-fav-btn")?.addEventListener("click",()=>removeFavoriteAndGoBack(pl.id));
  }else{
    $("#save-from-detail-btn")?.addEventListener("click", async e=>{
      const btn=e.currentTarget; btn.innerHTML=`<div class="spinner"></div>`;
      await api("save_playlist",pl);
      state.favorites[pl.id]=pl;
      showToast(t("addedPlaylistToFav"));
      renderFavorites(); renderPlaylistDetail(pl,true);
    });
  }
}

function renderTrackRow(track,idx,pl){
  const row=document.createElement("div");
  const blocked=!track.downloadable;
  row.className="track-row"+(blocked?" blocked":"");
  row.dataset.trackId=track.id;
  const metaParts=[];
  if(track.channel && track.channel!=="?") metaParts.push(escapeHtml(track.channel));
  if(track.views_display && track.views_display!=="?") metaParts.push(track.views_display);
  if(track.upload_date_display && track.upload_date_display!=="?") metaParts.push(track.upload_date_display);

  row.innerHTML=`
    <div class="track-num"><span class="track-index">${idx+1}</span><svg class="track-play-icon" viewBox="0 0 24 24" fill="currentColor"><path d="M8 5v14l11-7z"/></svg></div>
    <div class="track-title-cell"><div class="track-title">${escapeHtml(track.title)}</div>
      ${blocked?`<div class="track-reason">${escapeHtml(track.block_reason||t("notAvailable"))}</div>`:""}</div>
    <div class="track-meta-line">${metaParts.join(" • ")}</div>
    <div class="track-duration">${formatDuration(track.duration)}</div>
    <div class="track-actions"><button class="dl-track-btn ${track.downloaded?"downloaded":""}" title="${track.downloaded?t("alreadyDownloaded"):t("downloadBtn")}" ${blocked?"disabled":""}>
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">${track.downloaded?'<path d="M20 6L9 17l-5-5"/>':'<path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/>'}</svg>
    </button></div>`;

  row.addEventListener("click", e=>{
    if(e.target.closest(".track-actions")) return;
    if(blocked){ showToast(track.block_reason||t("trackUnavailable"),"warning"); return; }
    state.queue=pl.tracks; state.queueIndex=idx;
    playTrackAtQueueIndex(idx,pl);
  });
  if(!blocked){
    row.querySelector(".dl-track-btn").addEventListener("click", e=>{ e.stopPropagation(); downloadSingleTrack(track,pl,row); });
  }
  return row;
}

async function recheckOnePlaylist(pid){
  playerToast(t("checking"));
  try{
    const details=await api("fetch_playlist_details",state.favorites[pid].url,false);
    if(details===null){
      await api("mark_deleted",pid); state.favorites[pid].status="deleted";
      showToast(t("playlistDeleted"),"danger");
    }else{
      await api("save_playlist",details); state.favorites[pid]=details;
      showToast(t("playlistUpToDate"));
    }
    renderFavorites();
    if(state.currentPlaylistId===pid) renderPlaylistDetail(state.favorites[pid],true);
  }catch(err){
    await api("mark_deleted",pid); state.favorites[pid].status="deleted";
    renderFavorites(); showToast(t("playlistDeletedOrUnreachable"),"danger");
  }
}

async function removeFavoriteAndGoBack(pid){
  if(!confirm(t("confirmRemoveFav"))) return;
  await api("remove_playlist",pid);
  delete state.favorites[pid]; state.currentPlaylistId=null;
  renderFavorites(); switchView("search");
}

/* ---------- Lecture audio ---------- */
async function playTrackAtQueueIndex(idx,pl){
  const track=state.queue[idx];
  if(!track || !track.downloadable) return;
  updateNowPlayingUI(track,true);
  playerToastProgress(`${t("downloadingTemp")} 0%`,0);
  try{
    audio.src=track.id; // juste un marqueur non-vide pour satisfaire les checks existants
    await api("play_track",track.url,track.id); // télécharge (si besoin) ET lance la lecture côté Python
    audio._paused=false;
    state.isPlaying=true; updatePlayPauseIcon(); updateNowPlayingUI(track,false);
    playerToastProgress(null,null); playerToast(t("playingNow"),1200);
    $("#download-current-btn").disabled=false;
    $("#download-current-btn").onclick=()=>downloadSingleTrack(track, pl||{id:state.currentPlaylistId,title:""}, null);
    highlightPlayingRow(track.id);
  }catch(err){
    playerToastProgress(null,null);
    showToast(t("playbackImpossible")+" : "+err,"warning");
    track.downloadable=false; track.block_reason=String(err);
    if(pl) refreshTrackRow(track);
    autoAdvance();
  }
}

function highlightPlayingRow(trackId){
  $all(".track-row").forEach(r=>r.classList.remove("playing"));
  const row=document.querySelector(`.track-row[data-track-id="${trackId}"]`);
  if(row) row.classList.add("playing");
}
function refreshTrackRow(track){
  const row=document.querySelector(`.track-row[data-track-id="${track.id}"]`); if(!row) return;
  row.classList.add("blocked");
  const cell=row.querySelector(".track-title-cell");
  if(!cell.querySelector(".track-reason")){
    const div=document.createElement("div"); div.className="track-reason"; div.textContent=track.block_reason;
    cell.appendChild(div);
  }
  row.querySelector(".dl-track-btn").disabled=true;
}
function updateNowPlayingUI(track,loading){
  const hasThumb=!loading && track.thumbnail;
  $("#now-playing").innerHTML=`<div class="np-cover"${hasThumb?` style="background-image:url('${escapeHtml(track.thumbnail)}');background-size:cover;background-position:center"`:""}>${loading?'<div class="spinner"></div>':(hasThumb?"":"🎵")}</div>
    <div class="np-info"><div class="np-title">${escapeHtml(track.title)}</div><div class="np-sub">${loading?"Chargement...":"Lecture en cours"}</div></div>`;
}
function updatePlayPauseIcon(){ $("#play-icon").style.display=state.isPlaying?"none":"block"; $("#pause-icon").style.display=state.isPlaying?"block":"none"; }

$("#play-pause-btn").addEventListener("click",()=>{
  if(!audio.src) return;
  if(state.isPlaying){ audio.pause(); state.isPlaying=false; } else { audio.play(); state.isPlaying=true; }
  updatePlayPauseIcon();
});
$("#next-btn").addEventListener("click",()=>autoAdvance());
$("#prev-btn").addEventListener("click",()=>{ if(state.queueIndex>0){ state.queueIndex-=1; playTrackAtQueueIndex(state.queueIndex); } });

function autoAdvance(){
  if(state.queueIndex<state.queue.length-1){
    let next=state.queueIndex+1;
    while(next<state.queue.length && !state.queue[next].downloadable) next++;
    if(next<state.queue.length){ state.queueIndex=next; playTrackAtQueueIndex(next); }
  }
}
audio.addEventListener("ended", ()=>{ if(state.settings.autoplay) autoAdvance(); });
audio.addEventListener("timeupdate", ()=>{
  if(!audio.duration) return;
  $("#progress-fill").style.width=(audio.currentTime/audio.duration*100)+"%";
  $("#time-current").textContent=formatDuration(audio.currentTime);
  $("#time-total").textContent=formatDuration(audio.duration);
});
$("#progress-track").addEventListener("click", e=>{
  if(!audio.duration) return;
  const rect=e.currentTarget.getBoundingClientRect();
  audio.currentTime=((e.clientX-rect.left)/rect.width)*audio.duration;
});
$("#volume-track").addEventListener("click", e=>{
  const rect=e.currentTarget.getBoundingClientRect();
  const pct=Math.min(1,Math.max(0,(e.clientX-rect.left)/rect.width));
  audio.volume=pct; $("#volume-fill").style.width=(pct*100)+"%";
});

/* ---------- Téléchargements ---------- */
async function downloadSingleTrack(track,pl,rowEl){
  const btn=rowEl?rowEl.querySelector(".dl-track-btn"):$("#download-current-btn");
  const original=btn.innerHTML;
  btn.innerHTML=`<div class="spinner"></div>`; btn.disabled=true;
  try{
    const path=await api("download_track",track.url,pl.title||t("isolatedTrack"),pl.id);
    track.downloaded=true; track.local_path=path;
    showToast(`${t("downloaded")} : ${track.title}`);
    if(rowEl){
      btn.classList.add("downloaded");
      btn.innerHTML=`<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M20 6L9 17l-5-5"/></svg>`;
      btn.disabled=false;
    }else{ btn.innerHTML=original; btn.disabled=false; }
  }catch(err){
    showToast(t("downloadFailed")+" : "+err,"danger");
    btn.innerHTML=original; btn.disabled=false;
  }
}

async function downloadWholePlaylist(pl){
  const remaining=pl.tracks.filter(t=>t.downloadable && !t.downloaded);
  if(!confirm(`Télécharger les ${remaining.length} titres restants de « ${pl.title} » ?`)) return;
  const btn=$("#dl-all-btn");
  const total=remaining.length; let done=0;
  btn.disabled=true;
  for(const track of remaining){
    btn.innerHTML=`<div class="spinner"></div> ${done+1}/${total}`;
    try{
      const path=await api("download_track",track.url,pl.title,pl.id);
      track.downloaded=true; track.local_path=path;
      const row=document.querySelector(`.track-row[data-track-id="${track.id}"]`);
      if(row){
        const dlBtn=row.querySelector(".dl-track-btn");
        dlBtn.classList.add("downloaded");
        dlBtn.innerHTML=`<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M20 6L9 17l-5-5"/></svg>`;
      }
    }catch(err){
      track.downloadable=false; track.block_reason=String(err); refreshTrackRow(track);
    }
    done++;
  }
  btn.disabled=false;
  btn.innerHTML=`<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg> Télécharger tout`;
  showToast(`${t("downloadsFinished")} : ${done} ${t("tracksProcessed")}`);
}

/* ---------- Paramètres ---------- */
$("#settings-btn").addEventListener("click",()=>{
  $("#settings-btn").classList.add("spinning");
  setTimeout(()=>$("#settings-btn").classList.remove("spinning"),600);
  $("#settings-modal").classList.add("show");
});
$("#close-settings-btn").addEventListener("click",()=>$("#settings-modal").classList.remove("show"));
$("#settings-modal").addEventListener("click", e=>{ if(e.target.id==="settings-modal") $("#settings-modal").classList.remove("show"); });

$all(".swatch").forEach(sw=>{
  sw.addEventListener("click",()=>{
    $all(".swatch").forEach(s=>s.classList.remove("active"));
    sw.classList.add("active");
    const color=sw.dataset.color;
    document.documentElement.style.setProperty("--accent",color);
    document.documentElement.style.setProperty("--accent-h",color);
    state.settings.accent=color; persistSettings();
  });
});
$("#density-select").addEventListener("change", e=>{
  state.settings.density=e.target.value;
  const grid=$(".card-grid");
  if(grid){ const sizes={compact:130,normal:170,large:210}; grid.style.gridTemplateColumns=`repeat(auto-fill, minmax(${sizes[e.target.value]}px, 1fr))`; }
  persistSettings();
});
$("#quality-select").addEventListener("change", e=>{ state.settings.quality=e.target.value; api("set_setting","quality",e.target.value); persistSettings(); });
$("#language-select").addEventListener("change", e=>{
  state.settings.language=e.target.value;
  applyLanguage(state.settings.language);
  api("set_setting","language",state.settings.language); persistSettings();
});
$("#autoplay-toggle").addEventListener("click", e=>{ state.settings.autoplay=!state.settings.autoplay; e.target.classList.toggle("on",state.settings.autoplay); persistSettings(); });
$("#default-volume-select").addEventListener("change", e=>{
  state.settings.defaultVolume=parseFloat(e.target.value);
  audio.volume=state.settings.defaultVolume;
  $("#volume-fill").style.width=(state.settings.defaultVolume*100)+"%";
  persistSettings();
});
$("#organize-toggle").addEventListener("click", e=>{
  state.settings.organizeByPlaylist=!state.settings.organizeByPlaylist;
  e.target.classList.toggle("on",state.settings.organizeByPlaylist);
  api("set_setting","organizeByPlaylist",state.settings.organizeByPlaylist); persistSettings();
});
$("#reveal-toggle").addEventListener("click", e=>{
  state.settings.revealAfterDownload=!state.settings.revealAfterDownload;
  e.target.classList.toggle("on",state.settings.revealAfterDownload);
  api("set_setting","revealAfterDownload",state.settings.revealAfterDownload); persistSettings();
});
$("#autocheck-toggle").addEventListener("click", e=>{ state.settings.autocheck=!state.settings.autocheck; e.target.classList.toggle("on",state.settings.autocheck); persistSettings(); });
$("#choose-folder-btn").addEventListener("click", async ()=>{
  const folder=await api("choose_download_folder");
  if(folder){ state.settings.downloadFolder=folder; $("#download-folder-path").textContent=folder; persistSettings(); showToast(t("folderUpdated")); }
});
$("#clear-cache-btn").addEventListener("click", async ()=>{ await api("clear_temp_cache"); showToast(t("cacheCleared")); });
$("#reset-data-btn").addEventListener("click", async ()=>{
  if(!confirm(t("confirmReset"))) return;
  await api("reset_all_data"); state.favorites={}; renderFavorites(); switchView("search");
  showToast(t("allDataReset"));
});
function persistSettings(){ api("save_frontend_settings",state.settings); }

$("#back-btn").addEventListener("click",()=>switchView("search"));

/* ---------- Init ---------- */
async function init(){
  await backendReady();
  try{
    const [favs,settings]=await Promise.all([api("get_all_playlists"), api("get_frontend_settings")]);
    state.favorites=favs||{};
    if(settings){ state.settings={...state.settings,...settings}; applyLoadedSettings(); }
    renderFavorites();
    if(state.settings.autocheck) autoCheckAllFavorites();
  }catch(err){ console.error(err); }
}
function applyLoadedSettings(){
  document.documentElement.style.setProperty("--accent",state.settings.accent);
  document.documentElement.style.setProperty("--accent-h",state.settings.accent);
  audio.volume=state.settings.defaultVolume;
  $("#volume-fill").style.width=(state.settings.defaultVolume*100)+"%";
  $("#quality-select").value=state.settings.quality;
  $("#density-select").value=state.settings.density;
  $("#default-volume-select").value=String(state.settings.defaultVolume);
  $("#autoplay-toggle").classList.toggle("on",state.settings.autoplay);
  $("#organize-toggle").classList.toggle("on",state.settings.organizeByPlaylist);
  $("#reveal-toggle").classList.toggle("on",state.settings.revealAfterDownload);
  $("#autocheck-toggle").classList.toggle("on",state.settings.autocheck);
  $("#download-folder-path").textContent=state.settings.downloadFolder;
  $all(".swatch").forEach(s=>s.classList.toggle("active", s.dataset.color===state.settings.accent));
  $("#language-select").value=state.settings.language||"fr";
  applyLanguage(state.settings.language||"fr");
}
async function autoCheckAllFavorites(){
  for(const pid of Object.keys(state.favorites)){
    try{
      const details=await api("fetch_playlist_details",state.favorites[pid].url,false);
      if(details===null){ await api("mark_deleted",pid); state.favorites[pid].status="deleted"; }
      else{ await api("save_playlist",details); state.favorites[pid]=details; }
    }catch{ await api("mark_deleted",pid); state.favorites[pid].status="deleted"; }
    renderFavorites();
  }
}
init();
</script>
</body></html>
"""

MISSING = []
try:
    import yt_dlp
except ImportError:
    yt_dlp = None; MISSING.append("yt-dlp")
try:
    import webview
except ImportError:
    webview = None; MISSING.append("pywebview")
try:
    from mutagen.easyid3 import EasyID3
    from mutagen.id3 import ID3NoHeaderError
except ImportError:
    EasyID3 = None; ID3NoHeaderError = Exception; MISSING.append("mutagen")
try:
    import pygame
except ImportError:
    pygame = None; MISSING.append("pygame")


def tag_mp3(path, title=None, artist=None, album=None):
    """Écrit des tags ID3 propres (titre/artiste/album) pour que le MP3
    s'affiche correctement dans n'importe quel lecteur audio."""
    if EasyID3 is None:
        return
    try:
        try:
            tags = EasyID3(path)
        except ID3NoHeaderError:
            tags = EasyID3()
            tags.save(path)
            tags = EasyID3(path)
        if title: tags["title"] = title
        if artist: tags["artist"] = artist
        if album: tags["album"] = album
        tags.save()
    except Exception:
        pass  # le tag est un bonus, ne doit jamais faire échouer le téléchargement


# ------------------------------------------------------------------ Stockage
class JsonStore:
    def __init__(self, path: Path, default: dict):
        self.path = path
        self.lock = threading.Lock()
        self.data = json.loads(json.dumps(default))
        if path.exists():
            try:
                self.data = json.loads(path.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                pass
        for k, v in default.items():
            self.data.setdefault(k, v)

    def save(self):
        with self.lock:
            tmp = self.path.with_suffix(".json.tmp")
            tmp.write_text(json.dumps(self.data, ensure_ascii=False, indent=2), encoding="utf-8")
            os.replace(tmp, self.path)


class DataStore(JsonStore):
    def __init__(self, path):
        super().__init__(path, {"playlists": {}})

    def upsert(self, pl):
        pid = pl["id"]
        pl["status"] = "ok"
        pl["last_checked"] = datetime.now().isoformat()
        pl.setdefault("added_at", pl["last_checked"])
        self.data["playlists"][pid] = {**self.data["playlists"].get(pid, {}), **pl}
        self.save()

    def mark_deleted(self, pid):
        if pid in self.data["playlists"]:
            self.data["playlists"][pid]["status"] = "deleted"
            self.save()

    def remove(self, pid):
        self.data["playlists"].pop(pid, None)
        self.save()

    def reset(self):
        self.data = {"playlists": {}}
        self.save()


class SettingsStore(JsonStore):
    DEFAULTS = {
        "accent": "#1ed760", "density": "normal", "quality": "192",
        "autoplay": True, "defaultVolume": 0.8, "organizeByPlaylist": True,
        "revealAfterDownload": False, "autocheck": True,
        "downloadFolder": str(DEFAULT_DL_DIR), "language": "fr",
    }

    def __init__(self, path):
        super().__init__(path, dict(self.DEFAULTS))

    def folder(self) -> Path:
        # Si le dossier "Playlists" existe déjà à côté du script, on l'utilise
        # toujours en priorité — même si settings.json pointe ailleurs (ancien
        # réglage, dossier renommé/déplacé, etc). Ça évite de créer un second
        # dossier ("PlaylistsManager" ou autre) alors qu'un dossier valide existe déjà.
        if DEFAULT_DL_DIR.exists():
            return DEFAULT_DL_DIR
        f = self.data.get("downloadFolder")
        return Path(f) if f else DEFAULT_DL_DIR


# ------------------------------------------------------------------ yt-dlp
class YT:
    @staticmethod
    def _block_reason(e):
        if not e:
            return "Vidéo introuvable ou supprimée"
        av = e.get("availability")
        if av in ("private", "premium_only", "subscriber_only", "needs_auth"):
            return f"Accès restreint ({av})"
        if e.get("is_live"):
            return "Diffusion en direct (non téléchargeable)"
        if (e.get("age_limit") or 0) >= 18:
            return "Restriction d'âge"
        return None

    @staticmethod
    def _rel_date(d):
        if not d:
            return "?"
        try:
            dt = datetime.strptime(d, "%Y%m%d")
        except ValueError:
            return "?"
        days = (datetime.now() - dt).days
        if days < 1: return "aujourd'hui"
        if days < 30: return f"il y a {days} jour{'s' if days > 1 else ''}"
        if days < 365: return f"il y a {days // 30} mois"
        return f"il y a {days // 365} an{'s' if days // 365 > 1 else ''}"

    @staticmethod
    def _views(c):
        if not c: return "0 vue"
        for div, suf in ((1e9, "Md"), (1e6, "M"), (1e3, "k")):
            if c >= div: return f"{c/div:.1f} {suf} vues"
        return f"{c} vue{'s' if c > 1 else ''}"

    @staticmethod
    def _friendly_error(msg):
        low = msg.lower()
        if "sign in" in low or "private" in low: return "Vidéo privée ou nécessite une connexion"
        if "copyright" in low: return "Bloqué pour raison de droits d'auteur"
        if "unavailable" in low: return "Vidéo indisponible"
        return f"Échec : {msg[:180]}"

    @staticmethod
    def _best_thumbnail(e):
        """Extrait la meilleure URL de thumbnail disponible sur une entrée yt-dlp
        (vidéo ou playlist), qu'il s'agisse d'une liste 'thumbnails' ou d'un champ
        'thumbnail' direct."""
        if not e:
            return None
        thumbs = e.get("thumbnails")
        if thumbs:
            # trie par résolution décroissante et prend la meilleure valide
            try:
                thumbs = sorted(thumbs, key=lambda t: (t.get("width") or 0) * (t.get("height") or 0), reverse=True)
            except Exception:
                pass
            for t in thumbs:
                if t.get("url"): return t["url"]
        return e.get("thumbnail")

    @staticmethod
    def search_playlists(query, max_results=12):
        if yt_dlp is None: raise RuntimeError("yt-dlp n'est pas installé")
        q = urllib.parse.quote(query)
        url = f"https://www.youtube.com/results?search_query={q}&sp=EgIQAw%253D%253D"
        opts = {"quiet": True, "no_warnings": True, "extract_flat": True,
                "skip_download": True, "playlist_items": f"1-{max_results}"}
        try:
            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(url, download=False)
                entries = (info or {}).get("entries", [])
        except Exception as e:
            raise RuntimeError(f"Recherche impossible : {e}")
        out = []
        for e in entries:
            if not e or not e.get("id"): continue
            pid = e["id"]
            u = e.get("url") or f"https://www.youtube.com/playlist?list={pid}"
            if "list=" not in u: u = f"https://www.youtube.com/playlist?list={pid}"
            out.append({"id": pid, "title": e.get("title") or "(sans titre)", "url": u,
                        "channel": e.get("channel") or e.get("uploader") or "?",
                        "video_count": e.get("playlist_count") or e.get("entry_count"),
                        "thumbnail": YT._best_thumbnail(e)})
            if len(out) >= max_results: break
        return out

    @staticmethod
    def _unavailable(idx):
        return {"id": f"inconnu-{idx}", "title": "(Vidéo indisponible)", "url": None,
                "duration": 0, "channel": "?", "view_count": None, "views_display": "?",
                "upload_date_display": "?", "downloadable": False,
                "block_reason": "Vidéo supprimée ou rendue privée",
                "downloaded": False, "local_path": None, "thumbnail": None}

    @staticmethod
    def fetch_playlist_stub(url):
        """Récupère seulement les infos de la playlist (titre, auteur, nombre de
        vidéos) et la liste plate des titres, sans interroger chaque vidéo.
        Rapide : sert à afficher l'écran de playlist instantanément, puis les
        détails de chaque piste sont chargés par lots via fetch_track_batch."""
        if yt_dlp is None: raise RuntimeError("yt-dlp n'est pas installé")
        flat_opts = {"quiet": True, "no_warnings": True, "extract_flat": "in_playlist", "skip_download": True}
        with yt_dlp.YoutubeDL(flat_opts) as ydl:
            info = ydl.extract_info(url, download=False)
        if info is None: return None

        raw = info.get("entries", [])
        tracks = []
        for e in raw:
            if e is None:
                tracks.append(YT._unavailable(len(tracks))); continue
            reason = YT._block_reason(e)
            tracks.append({
                "id": e.get("id"), "title": e.get("title") or "(sans titre)",
                "url": e.get("url") or f"https://www.youtube.com/watch?v={e.get('id')}",
                "duration": e.get("duration") or 0,
                "channel": e.get("channel") or e.get("uploader") or "?",
                "view_count": e.get("view_count"), "views_display": YT._views(e.get("view_count")),
                "upload_date_display": "?", "downloadable": reason is None, "block_reason": reason,
                "downloaded": False, "local_path": None, "detailed": False,
                "thumbnail": YT._best_thumbnail(e)})

        # thumbnail de la playlist = celle de la première piste valide (sinon celle
        # éventuellement fournie par YouTube pour la playlist elle-même)
        first_track_thumb = next((t["thumbnail"] for t in tracks if t.get("thumbnail")), None)
        playlist_thumb = first_track_thumb or YT._best_thumbnail(info)

        return {"id": info.get("id"), "title": info.get("title") or "(playlist sans titre)", "url": url,
                "channel": info.get("channel") or info.get("uploader") or "?", "video_count": len(tracks),
                "total_views": None, "total_views_display": None, "tracks": tracks,
                "thumbnail": playlist_thumb}

    @staticmethod
    def fetch_track_batch(track_stubs):
        """Complète les infos (durée réelle, vues, date, disponibilité) pour un
        lot de pistes déjà obtenues via fetch_playlist_stub. Appelé par lots de
        10 depuis le frontend pour ne pas bloquer sur de grosses playlists."""
        if yt_dlp is None: raise RuntimeError("yt-dlp n'est pas installé")
        video_opts = {"quiet": True, "no_warnings": True, "skip_download": True, "noplaylist": True}
        out = []
        with yt_dlp.YoutubeDL(video_opts) as ydlv:
            for e in track_stubs:
                if not e.get("url"):
                    out.append(e); continue
                try:
                    vi = ydlv.extract_info(e["url"], download=False)
                except Exception as ex:
                    out.append({**e, "downloadable": False,
                                "block_reason": YT._friendly_error(str(ex)), "detailed": True})
                    continue
                reason = YT._block_reason(vi)
                out.append({
                    "id": e.get("id") or vi.get("id"), "title": vi.get("title") or e.get("title") or "(sans titre)",
                    "url": e["url"], "duration": vi.get("duration") or e.get("duration") or 0,
                    "channel": vi.get("channel") or vi.get("uploader") or e.get("channel") or "?",
                    "view_count": vi.get("view_count"), "views_display": YT._views(vi.get("view_count")),
                    "upload_date_display": YT._rel_date(vi.get("upload_date")),
                    "downloadable": reason is None, "block_reason": reason,
                    "downloaded": e.get("downloaded", False), "local_path": e.get("local_path"),
                    "thumbnail": YT._best_thumbnail(vi) or e.get("thumbnail"),
                    "detailed": True})
        return out

    @staticmethod
    def fetch_playlist_details(url, deep=True, progress_cb=None):
        """Conservé pour compatibilité (vérification au démarrage, etc.) —
        charge tout d'un coup. L'UI principale utilise désormais le chargement
        par lots (fetch_playlist_stub + fetch_track_batch)."""
        stub = YT.fetch_playlist_stub(url)
        if stub is None: return None
        if not deep:
            return stub
        total = len(stub["tracks"])
        detailed = []
        batch_size = 10
        for i in range(0, total, batch_size):
            batch = stub["tracks"][i:i + batch_size]
            detailed.extend(YT.fetch_track_batch(batch))
            if progress_cb: progress_cb(min(i + batch_size, total), total)
        stub["tracks"] = detailed
        views = [t["view_count"] for t in detailed if t.get("view_count")]
        total_views = sum(views) if views else None
        stub["total_views"] = total_views
        stub["total_views_display"] = YT._views(total_views) if total_views else None
        return stub

    @staticmethod
    def _with_retries(fn, max_attempts=3, on_retry=None):
        """Exécute fn() avec jusqu'à max_attempts tentatives. Relance l'exception
        d'origine si tous les essais échouent. on_retry(attempt, error) est appelé
        entre deux tentatives (pas après la dernière) pour informer l'UI."""
        last_err = None
        for attempt in range(1, max_attempts + 1):
            try:
                return fn()
            except Exception as e:
                last_err = e
                if attempt < max_attempts:
                    if on_retry:
                        try: on_retry(attempt, e)
                        except Exception: pass
                    __import__("time").sleep(1.5 * attempt)  # backoff progressif
        raise last_err

    @staticmethod
    def _extract_dl(video_url, dest_template, quality):
        opts = {"quiet": True, "no_warnings": True, "format": "bestaudio/best",
                "outtmpl": dest_template, "noplaylist": True,
                "postprocessors": [{"key": "FFmpegExtractAudio", "preferredcodec": "mp3",
                                     "preferredquality": quality}]}
        try:
            with yt_dlp.YoutubeDL(opts) as ydl:
                return ydl.extract_info(video_url, download=True)
        except yt_dlp.utils.DownloadError as e:
            raise RuntimeError(YT._friendly_error(str(e)))

    @staticmethod
    def download_temp_audio(video_url, quality="192", progress_cb=None, max_attempts=3):
        if yt_dlp is None: raise RuntimeError("yt-dlp n'est pas installé")

        total_bytes_transferred = {"n": 0}  # cumul réel sur toutes les tentatives (ce qui a vraiment transité)

        def make_hook():
            base = total_bytes_transferred["n"]  # octets déjà comptés lors des tentatives précédentes
            last_seen = {"n": 0}

            def hook(d):
                if progress_cb is None: return
                try:
                    if d.get("status") == "downloading":
                        downloaded = d.get("downloaded_bytes") or 0
                        total = d.get("total_bytes") or d.get("total_bytes_estimate")
                        pct = (downloaded / total * 100) if total else 0
                        speed = d.get("speed")
                        speed_txt = f"{speed/1024:.0f} Ko/s" if speed else ""
                        last_seen["n"] = downloaded
                        total_bytes_transferred["n"] = base + downloaded
                        progress_cb(pct, speed_txt, total_bytes_transferred["n"])
                    elif d.get("status") == "finished":
                        total_bytes_transferred["n"] = base + last_seen["n"]
                        progress_cb(100, "", total_bytes_transferred["n"])
                except Exception:
                    pass
            return hook

        def attempt():
            opts = {"quiet": True, "no_warnings": True, "format": "bestaudio/best",
                    "outtmpl": str(TEMP_DIR / "%(id)s.%(ext)s"), "noplaylist": True,
                    "progress_hooks": [make_hook()],
                    "postprocessors": [{"key": "FFmpegExtractAudio", "preferredcodec": "mp3",
                                         "preferredquality": quality}]}
            try:
                with yt_dlp.YoutubeDL(opts) as ydl:
                    return ydl.extract_info(video_url, download=True)
            except yt_dlp.utils.DownloadError as e:
                raise RuntimeError(YT._friendly_error(str(e)))

        def on_retry(attempt_no, err):
            if progress_cb:
                progress_cb(0, "", total_bytes_transferred["n"], retry=attempt_no, error=str(err))

        info = YT._with_retries(attempt, max_attempts=max_attempts, on_retry=on_retry)
        vid = info.get("id")
        final = TEMP_DIR / f"{vid}.mp3"
        path = str(final) if final.exists() else None
        if path is None:
            for f in TEMP_DIR.glob(f"{vid}.*"): path = str(f); break
        if path is None:
            raise RuntimeError("Fichier audio introuvable après téléchargement")
        tag_mp3(path, title=info.get("title"), artist=info.get("channel") or info.get("uploader"))
        return path, info.get("duration") or 0

    @staticmethod
    def download_permanent(video_url, dest_dir: Path, quality="192", playlist_title=None, playlist_author=None, max_attempts=3):
        """Télécharge d'abord dans un dossier temporaire, puis ne crée/déplace vers
        le dossier de la playlist qu'une fois le MP3 confirmé — pour ne jamais
        laisser un dossier de playlist vide si le téléchargement échoue."""
        if yt_dlp is None: raise RuntimeError("yt-dlp n'est pas installé")
        staging = TEMP_DIR / "staging"
        staging.mkdir(parents=True, exist_ok=True)
        info = YT._with_retries(lambda: YT._extract_dl(video_url, str(staging / "%(title)s.%(ext)s"), quality),
                                 max_attempts=max_attempts)
        title = info.get("title", "audio")
        cand = staging / f"{title}.mp3"
        staged_path = cand if cand.exists() else None
        if staged_path is None:
            mp3s = sorted(staging.glob("*.mp3"), key=lambda p: p.stat().st_mtime, reverse=True)
            if mp3s: staged_path = mp3s[0]
        if staged_path is None:
            raise RuntimeError("Fichier MP3 introuvable après téléchargement")
        # à ce stade seulement, on crée le dossier définitif et on y déplace le fichier
        dest_dir.mkdir(parents=True, exist_ok=True)
        final_path = dest_dir / staged_path.name
        shutil.move(str(staged_path), str(final_path))
        path = str(final_path)
        tag_mp3(path, title=title,
                artist=playlist_author or info.get("channel") or info.get("uploader"),
                album=playlist_title)
        return path


# ------------------------------------------------------------------ API JS
# ------------------------------------------------------------------ Lecteur audio (pygame)
# On lit les fichiers directement depuis le disque avec pygame.mixer, ce qui évite
# complètement le problème "NotSupportedError" de WebView2 avec <audio src="file://...">.
class Player:
    def __init__(self, get_window):
        self._get_window = get_window
        self._duration = 0.0
        self._offset = 0.0        # position (s) au dernier play/seek
        self._started_at = None   # time.time() du dernier resume ; None si en pause/stoppé
        self._path = None
        self._lock = threading.Lock()
        self._stop_ticker = threading.Event()
        if pygame is not None:
            pygame.mixer.init()
            threading.Thread(target=self._ticker_loop, daemon=True).start()

    def _elapsed(self):
        if self._started_at is None:
            return self._offset
        return self._offset + (__import__("time").time() - self._started_at)

    def _push(self, ended=False):
        win = self._get_window()
        if win is None: return
        try:
            win.evaluate_js(f"window.onPlayerTick&&window.onPlayerTick({self._elapsed():.2f},{self._duration:.2f},{'true' if ended else 'false'})")
        except Exception:
            pass

    def _ticker_loop(self):
        import time
        while not self._stop_ticker.is_set():
            time.sleep(0.25)
            with self._lock:
                if self._path is None:
                    continue
                if self._started_at is not None and not pygame.mixer.music.get_busy():
                    # la piste est terminée naturellement
                    self._offset = self._duration
                    self._started_at = None
                    self._push(ended=True)
                elif self._started_at is not None:
                    self._push(ended=False)

    def play(self, path, duration):
        if pygame is None: raise RuntimeError("pygame n'est pas installé")
        with self._lock:
            pygame.mixer.music.load(path)
            pygame.mixer.music.play()
            self._path = path
            self._duration = float(duration or 0)
            self._offset = 0.0
            self._started_at = __import__("time").time()

    def pause(self):
        if pygame is None: return
        with self._lock:
            if self._started_at is not None:
                self._offset = self._elapsed()
                self._started_at = None
            pygame.mixer.music.pause()

    def resume(self):
        if pygame is None: return
        with self._lock:
            if self._path is None: return
            pygame.mixer.music.unpause()
            self._started_at = __import__("time").time()

    def seek(self, seconds):
        if pygame is None or self._path is None: return
        with self._lock:
            seconds = max(0.0, min(float(seconds), self._duration or 0))
            try:
                pygame.mixer.music.play(start=seconds)
                self._offset = seconds
                self._started_at = __import__("time").time()
            except Exception:
                pass  # certains formats ne supportent pas 'start=' selon le backend SDL

    def set_volume(self, vol):
        if pygame is None: return
        try:
            pygame.mixer.music.set_volume(max(0.0, min(1.0, float(vol))))
        except Exception:
            pass

    def stop(self):
        if pygame is None: return
        with self._lock:
            pygame.mixer.music.stop()
            self._path = None; self._started_at = None; self._offset = 0.0


class API:
    def __init__(self):
        self.store = DataStore(DATA_FILE)
        self.settings = SettingsStore(SETTINGS_FILE)
        self.player = Player(lambda: webview.windows[0] if webview and webview.windows else None)

    def search_playlists(self, query):
        return YT.search_playlists(query)

    def fetch_playlist_details(self, url, deep=False):
        win = webview.windows[0] if webview.windows else None

        def progress(done, total):
            if win is None: return
            try:
                win.evaluate_js(f"window.onPlaylistFetchProgress&&window.onPlaylistFetchProgress({done},{total})")
            except Exception:
                pass

        return YT.fetch_playlist_details(url, deep=deep, progress_cb=progress if deep else None)

    def fetch_playlist_stub(self, url):
        """Chargement rapide et léger : infos playlist + titres bruts,
        sans interroger chaque vidéo. Utilisé pour l'affichage instantané."""
        return YT.fetch_playlist_stub(url)

    def fetch_track_batch(self, track_stubs):
        """Complète un lot de pistes (10 par défaut) avec durée/vues/date/
        disponibilité réelles. Appelé progressivement par le frontend."""
        return YT.fetch_track_batch(track_stubs)

    def add_playlist_from_link(self, url):
        if "list=" not in url and "playlist" not in url:
            raise Exception("Ce lien ne semble pas être une playlist YouTube (il doit contenir '?list=...')")
        return self.fetch_playlist_stub(url)

    def save_playlist(self, pl):
        self.store.upsert(pl); return True

    def remove_playlist(self, pid):
        self.store.remove(pid); return True

    def mark_deleted(self, pid):
        self.store.mark_deleted(pid); return True

    def get_all_playlists(self):
        return self.store.data["playlists"]

    def reset_all_data(self):
        self.store.reset(); return True

    def play_track(self, video_url, track_id):
        """Télécharge (si besoin, avec jusqu'à 3 tentatives) le fichier temporaire
        puis lance sa lecture via pygame, directement depuis le disque — pas de
        navigateur/WebView2 impliqué."""
        win = webview.windows[0] if webview and webview.windows else None

        def progress(pct, speed_txt, bytes_transferred=0, retry=None, error=None):
            if win is None: return
            try:
                win.evaluate_js(
                    f"window.onDownloadProgress&&window.onDownloadProgress("
                    f"{pct:.1f},{json.dumps(speed_txt)},{int(bytes_transferred)},"
                    f"{retry if retry is not None else 'null'},{json.dumps(error) if error else 'null'})")
            except Exception:
                pass

        path, duration = YT.download_temp_audio(video_url, self.settings.data.get("quality", "192"),
                                                  progress_cb=progress, max_attempts=3)
        self.player.play(path, duration)
        return {"duration": duration}

    def pause_audio(self):
        self.player.pause(); return True

    def resume_audio(self):
        self.player.resume(); return True

    def seek_audio(self, seconds):
        self.player.seek(seconds); return True

    def set_volume(self, vol):
        self.player.set_volume(vol); return True

    def stop_audio(self):
        self.player.stop(); return True

    def download_track(self, video_url, playlist_title, playlist_id, playlist_author=None):
        base = self.settings.folder()
        dest = base / self._safe_name(playlist_title) if self.settings.data.get("organizeByPlaylist", True) and playlist_title else base
        path = YT.download_permanent(video_url, dest, self.settings.data.get("quality", "192"),
                                      playlist_title=playlist_title, playlist_author=playlist_author)
        if self.settings.data.get("revealAfterDownload", False):
            self._reveal(path)
        return path

    def get_frontend_settings(self):
        return self.settings.data

    def save_frontend_settings(self, d):
        self.settings.data.update(d); self.settings.save(); return True

    def set_setting(self, key, value):
        self.settings.data[key] = value; self.settings.save(); return True

    def choose_download_folder(self):
        if webview is None: return None
        result = webview.windows[0].create_file_dialog(webview.FOLDER_DIALOG)
        if result:
            folder = result[0]
            self.settings.data["downloadFolder"] = folder
            self.settings.save()
            return folder
        return None

    def clear_temp_cache(self):
        n = 0
        for f in TEMP_DIR.glob("*"):
            try:
                f.unlink(); n += 1
            except OSError:
                pass
        return n

    @staticmethod
    def _safe_name(name):
        keep = "-_.() abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
        return ("".join(c if c in keep else "_" for c in name)).strip()[:80] or "playlist"

    @staticmethod
    def _reveal(path):
        try:
            import subprocess as sp
            if sys.platform == "win32": sp.run(["explorer", "/select,", path])
            elif sys.platform == "darwin": sp.run(["open", "-R", path])
            else: sp.run(["xdg-open", str(Path(path).parent)])
        except Exception:
            pass


def check_deps():
    problems = []
    if yt_dlp is None: problems.append("- Le module 'yt-dlp' n'est pas installé (pip install yt-dlp)")
    if webview is None: problems.append("- Le module 'pywebview' n'est pas installé (pip install pywebview)")
    if EasyID3 is None: problems.append("- Le module 'mutagen' n'est pas installé (pip install mutagen) — les MP3 seront téléchargés sans tags titre/artiste")
    if pygame is None: problems.append("- Le module 'pygame' n'est pas installé (pip install pygame) — nécessaire pour la lecture audio")
    if shutil.which("ffmpeg") is None: problems.append("- ffmpeg n'est pas trouvé dans le PATH")
    return problems


def main():
    problems = check_deps()
    if webview is None:
        msg = "Dépendances manquantes :\n" + "\n".join(problems) + \
              "\n\npip install yt-dlp pywebview mutagen pygame\nEt installe ffmpeg : https://ffmpeg.org/download.html"
        try:
            import tkinter as tk
            from tkinter import messagebox
            root = tk.Tk(); root.withdraw()
            messagebox.showerror("Dépendances manquantes", msg)
        except Exception:
            (APP_DIR / "erreur_dependances.txt").write_text(msg, encoding="utf-8")
        return

    api = API()
    html_path = TEMP_DIR / "index.html"
    html_path.write_text(INDEX_HTML, encoding="utf-8")
    window = webview.create_window(
        "Playlist Manager", url=str(html_path), js_api=api,
        width=1200, height=760, min_size=(900, 600), background_color="#000000", text_select=False)

    if problems:
        def warn():
            try:
                window.evaluate_js(
                    f"setTimeout(()=>window.showToast&&window.showToast({json.dumps(chr(10).join(problems))},'warning',8000),1500);")
            except Exception:
                pass
        threading.Timer(2.0, warn).start()

    webview.start()


if __name__ == "__main__":
    try:
        main()
    except Exception:
        err_path = APP_DIR / "erreur_log.txt"
        err_path.write_text(traceback.format_exc(), encoding="utf-8")
        try:
            import tkinter as tk
            from tkinter import messagebox
            root = tk.Tk(); root.withdraw()
            messagebox.showerror("Erreur fatale", f"Une erreur est survenue.\nDétails dans :\n{err_path}")
        except Exception:
            pass
