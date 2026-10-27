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

function NavLinkItem({ item }: { item: NavItem }) {
  const Glyph = item.icon
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
    return item.render({ className: classes.navItem, active: !!item.active, children: content })
  }
  return (
    <UnstyledButton
      className={classes.navItem}
      data-active={item.active || undefined}
      onClick={item.onSelect}
    >
      {content}
    </UnstyledButton>
  )
}

export function AppFrame({
  brand,
  navGroups,
  user,
  onSignOut,
  notifications = 0,
  searchPlaceholder = 'Search',
  children,
}: AppFrameProps) {
  return (
    <div className={classes.frame}>
      <div className={classes.brand}>
        <span className={classes.logo}>
          <SparkleIcon size={24} weight="fill" />
        </span>
        <div>
          <div className={classes.brandName}>{brand.name}</div>
          <div className={classes.brandSub}>{brand.subtitle}</div>
        </div>
      </div>
      <div className={classes.top}>
        <TextInput
          className={classes.search}
          variant="unstyled"
          placeholder={searchPlaceholder}
          leftSection={<MagnifyingGlassIcon size={18} />}
          aria-label={searchPlaceholder}
        />
        <div className={classes.topActions}>
          <ActionIcon variant="subtle" color="gray" size={32} aria-label="Help">
            <QuestionIcon size={18} />
          </ActionIcon>
          <Indicator label={notifications} disabled={notifications === 0} size={14} offset={3}>
            <ActionIcon variant="subtle" color="gray" size={32} aria-label="Notifications">
              <BellIcon size={18} />
            </ActionIcon>
          </Indicator>
          <span className={classes.divider} />
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
