import type { ReactElement, ReactNode } from 'react'
import {
  ActionIcon,
  Avatar,
  Badge,
  Indicator,
  Menu,
  SegmentedControl,
  TextInput,
  UnstyledButton,
  useMantineColorScheme,
} from '@mantine/core'
import {
  BellIcon,
  CaretDownIcon,
  MagnifyingGlassIcon,
  MoonIcon,
  QuestionIcon,
  SignOutIcon,
  SparkleIcon,
  SunIcon,
} from '@phosphor-icons/react'
import type { Icon } from '@phosphor-icons/react'
import classes from './AppFrame.module.css'

export type NavItem = {
  key: string
  label: string
  icon: Icon
  active?: boolean
  badge?: number
  onSelect?: () => void
  render?: (props: { className: string; active: boolean; children: ReactNode }) => ReactElement
}

export type AppFrameProps = {
  brand: { name: string; subtitle: string }
  navGroups: NavItem[][]
  user: { name: string; email: string }
  onSignOut: () => void
  notifications?: number
  searchPlaceholder?: string
  layout?: 'top' | 'side'
  children: ReactNode
}

function ThemeToggle() {
  const { colorScheme, setColorScheme } = useMantineColorScheme()
  return (
    <SegmentedControl
      size="xs"
      radius="xl"
      value={colorScheme === 'dark' ? 'dark' : 'light'}
      onChange={(value) => setColorScheme(value === 'dark' ? 'dark' : 'light')}
      data={[
        { value: 'light', label: <SunIcon size={16} aria-label="Light theme" /> },
        { value: 'dark', label: <MoonIcon size={16} aria-label="Dark theme" /> },
      ]}
    />
  )
}

function NavLinkItem({ item, pill }: { item: NavItem; pill?: boolean }) {
  const Glyph = item.icon
  const className = pill ? classes.pillItem : classes.navItem
  const content = (
    <>
      <Glyph size={18} weight={item.active ? 'fill' : 'regular'} />
      <span className={classes.navLabel}>{item.label}</span>
      {item.badge ? (
        <Badge size="sm" circle>
          {item.badge}
        </Badge>
      ) : null}
    </>
  )
  if (item.render) {
    return item.render({ className, active: !!item.active, children: content })
  }
  return (
    <UnstyledButton className={className} data-active={item.active || undefined} onClick={item.onSelect}>
      {content}
    </UnstyledButton>
  )
}

function Actions({ notifications }: { notifications: number }) {
  return (
    <>
      <ActionIcon variant="subtle" color="gray" size={32} aria-label="Help">
        <QuestionIcon size={18} />
      </ActionIcon>
      <Indicator label={notifications} disabled={notifications === 0} size={14} offset={3}>
        <ActionIcon variant="subtle" color="gray" size={32} aria-label="Notifications">
          <BellIcon size={18} />
        </ActionIcon>
      </Indicator>
    </>
  )
}

function UserMenu({ user, onSignOut }: Pick<AppFrameProps, 'user' | 'onSignOut'>) {
  return (
    <Menu position="bottom-end" width={200}>
      <Menu.Target>
        <UnstyledButton className={classes.userButton}>
          <Avatar color="brand" radius="xl" size={28}>
            {user.name.slice(0, 1)}
          </Avatar>
          <div>
            <div className={classes.userName}>{user.name}</div>
            <div className={classes.userMail}>{user.email}</div>
          </div>
          <CaretDownIcon size={14} />
        </UnstyledButton>
      </Menu.Target>
      <Menu.Dropdown>
        <Menu.Item leftSection={<SignOutIcon size={16} />} onClick={onSignOut}>
          Sign out
        </Menu.Item>
      </Menu.Dropdown>
    </Menu>
  )
}

function Logo() {
  return (
    <span className={classes.logo}>
      <SparkleIcon size={16} weight="fill" />
    </span>
  )
}

export function AppFrame({
  brand,
  navGroups,
  user,
  onSignOut,
  notifications = 0,
  searchPlaceholder = 'Search',
  layout = 'side',
  children,
}: AppFrameProps) {
  const search = (
    <TextInput
      className={layout === 'top' ? classes.searchPill : classes.search}
      variant={layout === 'top' ? 'filled' : 'unstyled'}
      radius="xl"
      placeholder={searchPlaceholder}
      leftSection={<MagnifyingGlassIcon size={18} />}
      aria-label={searchPlaceholder}
    />
  )

  if (layout === 'top') {
    return (
      <div className={classes.topFrame}>
        <header className={classes.topBar}>
          <div className={classes.brandPill}>
            <Logo />
            <span className={classes.brandName}>{brand.name}</span>
          </div>
          <nav className={classes.pills} aria-label="Main">
            {navGroups.flat().map((item) => (
              <NavLinkItem key={item.key} item={item} pill />
            ))}
          </nav>
          <div className={classes.topActions}>
            {search}
            <Actions notifications={notifications} />
            <ThemeToggle />
            <UserMenu user={user} onSignOut={onSignOut} />
          </div>
        </header>
        <main className={classes.topMain}>{children}</main>
      </div>
    )
  }

  return (
    <div className={classes.frame}>
      <div className={classes.brand}>
        <Logo />
        <div>
          <div className={classes.brandName}>{brand.name}</div>
          <div className={classes.brandSub}>{brand.subtitle}</div>
        </div>
      </div>
      <div className={classes.top}>
        {search}
        <div className={classes.topActions}>
          <Actions notifications={notifications} />
          <span className={classes.divider} />
          <UserMenu user={user} onSignOut={onSignOut} />
        </div>
      </div>
      <nav className={classes.side} aria-label="Main">
        {navGroups.map((group, index) => (
          <div key={index} className={classes.navGroup}>
            <div className={classes.nav}>
              {group.map((item) => (
                <NavLinkItem key={item.key} item={item} />
              ))}
            </div>
          </div>
        ))}
        <div className={classes.sideFooter}>
          <ThemeToggle />
        </div>
      </nav>
      <main className={classes.main}>{children}</main>
    </div>
  )
}
