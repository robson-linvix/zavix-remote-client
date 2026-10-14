//! Minimal native GTK interface for the assisted Linux x86 client.
use crate::ui_cm_interface::{self as cm, Client, ConnectionManager, InvokeUiCM};
use gtk::{glib, prelude::*};
use hbb_common::{bail, config, log, ResultType};
use std::{collections::HashMap, sync::mpsc, time::{Duration, SystemTime, UNIX_EPOCH}};

#[derive(Clone)]
struct GtkHandler(mpsc::Sender<Event>);

enum Event {
    Connection(Client),
    Remove(i32),
    Message(String),
}

impl GtkHandler {
    fn send(&self, event: Event) {
        if self.0.send(event).is_err() {
            log::debug!("GTK window closed before notification delivery");
        }
    }
}

impl InvokeUiCM for GtkHandler {
    fn add_connection(&self, client: &Client) {
        if client.is_file_transfer || client.is_view_camera || client.is_terminal
            || !client.port_forward.is_empty() || cm::get_clients_length() > 1 {
            cm::close(client.id);
            return;
        }
        self.send(Event::Connection(client.clone()));
    }
    fn remove_connection(&self, id: i32, _close: bool) {
        cm::remove(id);
        self.send(Event::Remove(id));
    }
    fn new_message(&self, _id: i32, text: String) {
        self.send(Event::Message(text.chars().take(2000).collect()));
    }
    // This small client has a fixed Portuguese interface and no elevated/audio/file modes.
    fn change_theme(&self, _dark: String) {}
    fn change_language(&self) {}
    fn show_elevation(&self, _show: bool) {}
    fn update_voice_call_state(&self, _client: &Client) {}
    fn file_transfer_log(&self, _action: &str, _log: &str) {}
}

fn text(value: &str) -> gtk::Label {
    let label = gtk::Label::new(Some(value));
    label.set_xalign(0.0);
    label.set_line_wrap(true);
    label.set_max_width_chars(48);
    label
}

fn request_row(client: &Client) -> gtk::Box {
    let row = gtk::Box::new(gtk::Orientation::Vertical, 10);
    row.pack_start(&text(&format!("Solicitação de {} · ID {}", client.name, client.peer_id)), false, false, 0);
    let status = text(if client.authorized { "Conexão autorizada" } else { "Permitir acesso à tela, ao teclado e ao mouse?" });
    row.pack_start(&status, false, false, 0);
    let actions = gtk::Box::new(gtk::Orientation::Horizontal, 12);
    if !client.authorized {
        let accept = gtk::Button::with_mnemonic("_Aceitar");
        accept.style_context().add_class("suggested-action");
        let id = client.id;
        let status = status.clone();
        accept.connect_clicked(move |button| {
            button.set_sensitive(false);
            let clicked = SystemTime::now().duration_since(UNIX_EPOCH).map(|v| v.as_millis() as i64).unwrap_or(0);
            cm::check_click_time(id);
            let button = button.clone();
            let status = status.clone();
            glib::timeout_add_local_once(Duration::from_millis(150), move || {
                if clicked.saturating_sub(cm::get_click_time()) > 120 {
                    cm::authorize(id);
                    status.set_text("Conexão autorizada. Você pode encerrá-la abaixo.");
                } else {
                    status.set_text("Aceite a solicitação diretamente neste computador.");
                    button.set_sensitive(true);
                }
            });
        });
        actions.pack_start(&accept, false, false, 0);
    }
    let close = gtk::Button::with_mnemonic(if client.authorized { "_Encerrar conexão" } else { "_Recusar / encerrar" });
    let id = client.id;
    close.connect_clicked(move |button| {
        cm::close(id);
        button.set_sensitive(false);
    });
    actions.pack_start(&close, false, false, 0);
    row.pack_start(&actions, false, false, 0);
    row
}

pub fn run() -> ResultType<()> {
    let args: Vec<String> = std::env::args().skip(1).collect();
    if args.iter().any(|arg| !matches!(arg.as_str(), "--no-server" | "--cm" | "--zavix-diagnostics" | "--version")) {
        bail!("Este cliente oferece somente atendimento assistido com aceite local.");
    }
    if args.iter().any(|arg| arg == "--zavix-diagnostics" || arg == "--version") {
        crate::core_main::core_main();
        return Ok(());
    }
    if std::env::var("XDG_SESSION_TYPE").as_deref() == Ok("wayland") {
        bail!("Esta versão requer uma sessão X11. Wayland não está homologado.");
    }
    gtk::init()?;
    let application = gtk::Application::new(Some("app.zavix.remote.linux32"), gtk::gio::ApplicationFlags::empty());
    application.register(None::<&gtk::gio::Cancellable>)?;
    if application.is_remote() {
        application.activate();
        return Ok(());
    }
    if crate::core_main::core_main().is_none() {
        return Ok(());
    }
    crate::ui_interface::start_option_status_sync();
    let (sender, receiver) = mpsc::channel();
    let handler = GtkHandler(sender);
    std::thread::spawn(move || cm::start_ipc(ConnectionManager { ui_handler: handler }));
    let window = gtk::Window::new(gtk::WindowType::Toplevel);
    window.set_application(Some(&application));
    let active_window = window.clone();
    application.connect_activate(move |_| active_window.present());
    window.set_title("ZAVIX Remote — Linux 32 bits");
    window.set_default_size(470, 470);
    window.set_position(gtk::WindowPosition::Center);
    window.set_border_width(24);
    let layout = gtk::Box::new(gtk::Orientation::Vertical, 16);
    if let Ok(executable) = std::env::current_exe() {
        let icon = executable.with_file_name("zavix.png");
        if icon.is_file() {
            let image = gtk::Image::from_file(icon);
            image.set_halign(gtk::Align::Start);
            layout.pack_start(&image, false, false, 0);
        }
    }
    let title = text("ZAVIX Remote · Assistência remota");
    title.style_context().add_class("title");
    layout.pack_start(&title, false, false, 0);
    layout.pack_start(&text("Versão candidata · Debian 12 · x86/i686 · X11\nInforme seu ID ao atendente e aceite a solicitação neste computador."), false, false, 0);
    let id = text("Gerando ID…");
    id.set_selectable(true);
    layout.pack_start(&id, false, false, 0);
    let state = text("Conectando ao servidor…");
    layout.pack_start(&state, false, false, 0);
    let requests = gtk::Box::new(gtk::Orientation::Vertical, 12);
    layout.pack_start(&requests, false, false, 0);
    let message = text("");
    layout.pack_start(&message, false, false, 0);
    layout.pack_start(&text("Um atendimento por vez. Sem acesso não supervisionado. Fechar o aplicativo encerra o atendimento."), false, false, 0);
    let exit = gtk::Button::with_mnemonic("_Sair e encerrar atendimento");
    exit.connect_clicked(|_| gtk::main_quit());
    layout.pack_start(&exit, false, false, 0);
    window.add(&layout);
    window.connect_delete_event(|_, _| {
        gtk::main_quit();
        glib::Propagation::Proceed
    });
    window.show_all();
    let mut rows: HashMap<i32, gtk::Box> = HashMap::new();
    glib::timeout_add_local(Duration::from_millis(200), move || {
        let own_id = config::Config::get_id();
        id.set_text(if own_id.is_empty() { "Gerando ID…" } else { &own_id });
        state.set_text(if crate::ui_interface::get_connect_status().status_num > 0 { "Pronto para receber atendimento" } else { "Conectando ao servidor…" });
        for event in receiver.try_iter() {
            match event {
                Event::Connection(client) => {
                    if let Some(old) = rows.remove(&client.id) { requests.remove(&old); }
                    let row = request_row(&client);
                    requests.pack_start(&row, false, false, 0);
                    rows.insert(client.id, row);
                    requests.show_all();
                    window.present();
                }
                Event::Remove(id) => {
                    if let Some(row) = rows.remove(&id) { requests.remove(&row); }
                    message.set_text("Atendimento encerrado.");
                }
                Event::Message(value) => message.set_text(&value),
            }
        }
        glib::ControlFlow::Continue
    });
    gtk::main();
    crate::common::global_clean();
    Ok(())
}
