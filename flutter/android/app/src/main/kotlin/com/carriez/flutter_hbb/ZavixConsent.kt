package com.carriez.flutter_hbb

import android.app.Activity
import android.app.AlertDialog

object ZavixConsent {
    fun screen(activity: Activity, accept: () -> Unit, cancel: () -> Unit) {
        AlertDialog.Builder(activity)
            .setTitle("Compartilhar a tela com o suporte ZAVIX?")
            .setMessage("Durante a assistência, o conteúdo visível da sua tela será transmitido ao atendente por nossa infraestrutura ZAVIX Remote. Isso pode incluir mensagens e dados pessoais que você abrir. Feche informações sensíveis antes de continuar. Este piloto não grava a tela. Você pode encerrar o atendimento no aplicativo a qualquer momento. Na próxima tela, confirme também a autorização do Android.")
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
