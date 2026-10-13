package com.carriez.flutter_hbb

import android.app.Activity
import android.app.AlertDialog
import android.content.Context
import android.os.Build

object ZavixConsent {
    fun screen(activity: Activity, accept: () -> Unit, cancel: () -> Unit) {
        if (BuildConfig.ZAVIX_MANAGED && Build.VERSION.SDK_INT <= Build.VERSION_CODES.P &&
            activity.intent.getBooleanExtra(EXT_INIT_FROM_BOOT, false) &&
            activity.getSharedPreferences(KEY_SHARED_PREFERENCES, Context.MODE_PRIVATE)
                .getBoolean(KEY_START_ON_BOOT_OPT, false)) {
            accept()
            return
        }
        AlertDialog.Builder(activity)
            .setTitle("Preparar captura para o ZAVIX Remote?")
            .setMessage("Autorize a captura inicial do equipamento. O acesso remoto utilizará a senha individual configurada neste aparelho. A captura pode encerrar outra assistência ativa, incluindo a SUNMI: conclua a configuração e teste somente o ZAVIX. Na próxima tela, confirme a permissão do Android; se houver a opção de lembrar a autorização, ela pode ser usada para o equipamento administrado. A gravação permanece desligada.")
            .setPositiveButton("Continuar") { _, _ -> accept() }
            .setNegativeButton("Cancelar") { _, _ -> cancel() }
            .setOnCancelListener { cancel() }
            .show()
    }

    fun control(activity: Activity, accept: () -> Unit) {
        AlertDialog.Builder(activity)
            .setTitle("Permitir controle remoto autorizado?")
            .setMessage("O ZAVIX Remote usa o serviço de acessibilidade para permitir ao atendente autorizado acessar elementos e textos visíveis na tela e executar toques, rolagem e digitação durante a assistência. Essas informações e ações são utilizadas para prestar suporte remoto. Não habilite este acesso por solicitação de desconhecidos. Você pode desativar o controle nas configurações do Android ou encerrar a assistência no aplicativo. O controle é opcional: compartilhar a tela não exige habilitá-lo.")
            .setPositiveButton("Abrir configurações") { _, _ -> accept() }
            .setNegativeButton("Agora não", null)
            .show()
    }
}
