import { AlertCircle, Eye, EyeOff, LifeBuoy, MessageCircle, Package } from 'lucide-react'
import { useState, type FormEvent } from 'react'
import { useAuth } from '../../app/providers/auth-context'
import { Button } from '../../components/ui/Button'
import { Logo } from '../../components/ui/Logo'
import { TextField } from '../../components/ui/TextField'
import { ApiRequestError } from '../../lib/api/client'
import styles from './LoginPage.module.css'

const BENEFITS = [
  { icon: Package, text: 'Acompanhe cada pedido, do aceite à entrega.' },
  { icon: MessageCircle, text: 'Converse com o comprador no contexto do item.' },
  { icon: LifeBuoy, text: 'Veja primeiro o que o atendimento precisa resolver.' },
]

export function LoginPage() {
  const { login } = useAuth()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [passwordVisible, setPasswordVisible] = useState(false)
  const [fieldErrors, setFieldErrors] = useState<{ email?: string; password?: string }>({})
  const [error, setError] = useState<string | null>(null)
  const [submitting, setSubmitting] = useState(false)

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()

    // Validacao no cliente antes de chamar a API: sem ela, campo vazio
    // voltava como erro de schema do backend, em ingles e por campo.
    const nextFieldErrors = {
      email: email.trim() ? undefined : 'Informe seu email.',
      password: password ? undefined : 'Informe sua senha.',
    }
    setFieldErrors(nextFieldErrors)
    if (nextFieldErrors.email || nextFieldErrors.password) {
      setError(null)
      return
    }

    setError(null)
    setSubmitting(true)
    try {
      await login(email, password)
    } catch (err) {
      if (err instanceof ApiRequestError) {
        // Mensagem de erro da API e contrato em ingles, para quem consome.
        // Quem esta na tela recebe a versao em portugues.
        setError(
          err.code === 'unauthorized'
            ? 'Email ou senha inválidos.'
            : 'Não foi possível entrar agora. Tente de novo em instantes.',
        )
      } else {
        setError('Não foi possível conectar à API.')
      }
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className={styles.page}>
      <section className={styles.brand}>
        <div className={styles.brandInner}>
          <Logo size="md" />
          <h1 className={styles.headline}>Sua operação de marketplace em um lugar só.</h1>
          <ul className={styles.benefits}>
            {BENEFITS.map((benefit) => {
              const Icon = benefit.icon
              return (
                <li key={benefit.text} className={styles.benefit}>
                  <span className={styles.benefitIcon} aria-hidden="true">
                    <Icon size={18} />
                  </span>
                  {benefit.text}
                </li>
              )
            })}
          </ul>
        </div>
      </section>

      <div className={styles.formSide}>
        <div className={styles.card}>
          <div className={styles.heading}>
            <h2>Entrar</h2>
            <p className={styles.subtitle}>
              Use a conta que a sua loja ou o time de operações criou.
            </p>
          </div>

          <form className={styles.form} onSubmit={handleSubmit} noValidate>
            <TextField
              label="Email"
              type="email"
              name="email"
              autoComplete="username"
              autoFocus
              value={email}
              onChange={(event) => setEmail(event.target.value)}
              error={fieldErrors.email}
              required
            />
            <TextField
              label="Senha"
              type={passwordVisible ? 'text' : 'password'}
              name="password"
              autoComplete="current-password"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              error={fieldErrors.password}
              required
              trailing={
                <button
                  type="button"
                  className={styles.toggleVisibility}
                  onClick={() => setPasswordVisible((visible) => !visible)}
                  aria-label={passwordVisible ? 'Ocultar senha' : 'Mostrar senha'}
                  aria-pressed={passwordVisible}
                >
                  {passwordVisible ? (
                    <EyeOff size={18} aria-hidden="true" />
                  ) : (
                    <Eye size={18} aria-hidden="true" />
                  )}
                </button>
              }
            />

            {error && (
              <p className={styles.alert} role="alert">
                <AlertCircle size={18} className={styles.alertIcon} aria-hidden="true" />
                {error}
              </p>
            )}

            <Button type="submit" loading={submitting} fullWidth>
              Entrar
            </Button>
          </form>

          <p className={styles.footnote}>
            Comprador, vendedor e operações entram pela mesma porta. O papel vem da conta.
          </p>
        </div>
      </div>
    </div>
  )
}
