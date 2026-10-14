# Cinematic prison menu

The exploration title/pause menus and chapter story title/pause menus now use the supplied reference’s direction: an atmospheric night view of Alcatraz, dark sidebar, large condensed cream headings, warm gold rules, illustrated navigation and a highlighted active menu page. The exploration overview includes five activity icons. Existing location travel, settings, controls, checkpoint and scene actions remain connected.

Menu text and buttons are rendered by Unity independently of the background. The background is newly generated decorative concept artwork inspired by the reference; it does not depict the game’s runtime rendering. Icons are original line drawings authored by Tools/author_menu_assets.py. Anton is distributed under the SIL Open Font License; the license is in MenuFontLicense.txt and its source is https://github.com/google/fonts/tree/main/ofl/anton.

Both menu callers use a uniform 1920 × 1080 reference canvas with centred fitting and black margins on differing aspect ratios. The exploration gameplay HUD continues using its own existing viewport. Menu actions remain usable on smaller windows; extreme portrait aspect ratios display a smaller fitted menu rather than reflowing the columns.

[Offline layout preview](CinematicMenuPreview.html) is an HTML approximation using the committed art, icons and font. Generate it with Tools/create_menu_preview.py. This preview is not a Unity screenshot or a second implementation of gameplay actions.

C# grammar parsing passed for all 77 files, and the scratch checkout containing the new menu resources passed native asset integrity checks with zero errors. The HTML preview loaded all icons and the Anton font and fitted 1920 × 1080, 1280 × 720, 3440 × 1440 and 1024 × 768 windows. Results are saved in Validation/CinematicMenuChecks.json. Unity import, final font metrics, menu click targets and gameplay transitions still need Unity validation because the editor is unavailable here.
